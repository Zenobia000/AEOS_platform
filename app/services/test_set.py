"""TestSet service — case CRUD + run lifecycle (S3 / AC-001).

對應 PRD-001 §5.2 F-TS-01/02/03:
- F-TS-01: Expert 輸入 50 題 test_case
- F-TS-02: Worker 批次跑 → 算 pass_rate
- F-TS-03: pass_rate ≥ 0.80 才允許 Skill 升 production

審計：start_test_run / complete_test_run 進 audit_log（test_run.started /
test_run.completed）。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.test_case import TestCase
from app.db.models.test_run import TestRun
from app.db.models.test_run_case import TestRunCase
from app.services import audit


class TestSetError(RuntimeError):
    """Test set 動作無法執行（state 不對 / 不存在等）."""


@dataclass(frozen=True)
class RunSummary:
    run_id: uuid.UUID
    status: Literal["pending", "running", "completed", "failed"]
    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: float


# ── test_case CRUD ──────────────────────────────────


async def create_test_case(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    name: str,
    user_input: str,
    expected_outcome: str,
    expected_keywords: list[str] | None = None,
    created_by: str | None = None,
    skill_slug: str | None = None,
) -> TestCase:
    if not name.strip():
        raise TestSetError("name cannot be empty")
    if not user_input.strip():
        raise TestSetError("user_input cannot be empty")
    if not expected_outcome.strip():
        raise TestSetError("expected_outcome cannot be empty")

    tc = TestCase(
        tenant_id=tenant_id,
        name=name.strip(),
        user_input=user_input,
        expected_outcome=expected_outcome,
        expected_keywords=expected_keywords or [],
        created_by=created_by,
        skill_slug=skill_slug,
    )
    session.add(tc)
    await session.flush()
    return tc


async def list_test_cases(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    enabled_only: bool = True,
    skill_slug: str | None = None,
    limit: int = 200,
) -> list[TestCase]:
    """List test cases. 若 skill_slug 提供 → 列該 skill + NULL 通用題；None → 全列。"""
    from sqlalchemy import or_

    stmt = select(TestCase).where(TestCase.tenant_id == tenant_id)
    if enabled_only:
        stmt = stmt.where(TestCase.enabled.is_(True))
    if skill_slug is not None:
        stmt = stmt.where(or_(TestCase.skill_slug == skill_slug, TestCase.skill_slug.is_(None)))
    stmt = stmt.order_by(TestCase.created_at.asc()).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def disable_test_case(
    session: AsyncSession,
    *,
    test_case_id: uuid.UUID,
) -> TestCase:
    tc = (
        await session.execute(select(TestCase).where(TestCase.id == test_case_id))
    ).scalar_one_or_none()
    if tc is None:
        raise TestSetError(f"test_case {test_case_id} not found")
    tc.enabled = False
    await session.flush()
    return tc


# ── test_run lifecycle ─────────────────────────────


async def create_test_run(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    skill_slug: str,
    skill_version: str,
    created_by: str | None = None,
) -> TestRun:
    """建一個 pending run + 填入該 tenant 所有 enabled cases 為 test_run_case."""
    cases = await list_test_cases(session, tenant_id=tenant_id, enabled_only=True)
    if not cases:
        raise TestSetError(f"no enabled test_case for tenant {tenant_id}; cannot create run")

    run = TestRun(
        tenant_id=tenant_id,
        skill_slug=skill_slug,
        skill_version=skill_version,
        status="pending",
        total_cases=len(cases),
        created_by=created_by,
    )
    session.add(run)
    await session.flush()

    for c in cases:
        session.add(
            TestRunCase(
                test_run_id=run.id,
                test_case_id=c.id,
                status="pending",
            )
        )
    await session.flush()

    await audit.emit(
        session,
        event_type="test_run.created",
        tenant_id=tenant_id,
        actor_id=created_by or "system",
        resource_type="test_run",
        resource_id=str(run.id),
        payload={
            "skill_slug": skill_slug,
            "skill_version": skill_version,
            "total_cases": len(cases),
        },
    )
    return run


async def mark_run_running(session: AsyncSession, *, run_id: uuid.UUID) -> TestRun:
    run = (await session.execute(select(TestRun).where(TestRun.id == run_id))).scalar_one_or_none()
    if run is None:
        raise TestSetError(f"test_run {run_id} not found")
    if run.status != "pending":
        raise TestSetError(f"test_run {run_id} not in pending (status={run.status})")
    run.status = "running"
    run.started_at = datetime.now(UTC)
    await session.flush()
    return run


async def finalize_run(
    session: AsyncSession,
    *,
    run_id: uuid.UUID,
) -> RunSummary:
    """從 test_run_case 聚合算 pass/fail/score → 更新 test_run + audit."""
    run = (await session.execute(select(TestRun).where(TestRun.id == run_id))).scalar_one_or_none()
    if run is None:
        raise TestSetError(f"test_run {run_id} not found")

    counts = (
        await session.execute(
            select(TestRunCase.status, func.count(TestRunCase.test_case_id))
            .where(TestRunCase.test_run_id == run_id)
            .group_by(TestRunCase.status)
        )
    ).all()

    by_status: dict[str, int] = {s: int(c) for s, c in counts}
    passed = by_status.get("passed", 0)
    failed = by_status.get("failed", 0) + by_status.get("error", 0)
    total = run.total_cases or (passed + failed + by_status.get("pending", 0))
    pass_rate = (passed / total) if total else 0.0

    run.passed_cases = passed
    run.failed_cases = failed
    run.pass_rate = pass_rate
    run.status = "completed" if (passed + failed) == total else "failed"
    run.completed_at = datetime.now(UTC)
    await session.flush()

    await audit.emit(
        session,
        event_type="test_run.completed",
        tenant_id=run.tenant_id,
        actor_id="test_runner",
        resource_type="test_run",
        resource_id=str(run.id),
        payload={
            "passed": passed,
            "failed": failed,
            "total": total,
            "pass_rate": pass_rate,
        },
    )

    return RunSummary(
        run_id=run.id,
        status=run.status,  # type: ignore[arg-type]
        total_cases=total,
        passed_cases=passed,
        failed_cases=failed,
        pass_rate=pass_rate,
    )


async def get_run_summary(session: AsyncSession, *, run_id: uuid.UUID) -> RunSummary:
    run = (await session.execute(select(TestRun).where(TestRun.id == run_id))).scalar_one_or_none()
    if run is None:
        raise TestSetError(f"test_run {run_id} not found")
    return RunSummary(
        run_id=run.id,
        status=run.status,  # type: ignore[arg-type]
        total_cases=run.total_cases,
        passed_cases=run.passed_cases,
        failed_cases=run.failed_cases,
        pass_rate=run.pass_rate,
    )
