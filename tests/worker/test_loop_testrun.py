"""Worker loop test-run cycle 測試 — auto-pick pending test_run."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import InternalToolRegistry
from app.agent.builtin_tools import register_builtins
from app.db.models.tenant import Tenant
from app.db.models.test_run import TestRun
from app.llm.client import LLMClient, LLMResponse, LLMUsage
from app.services import test_set
from app.skill import SkillLoader
from app.worker.draft_processor import DraftProcessor
from app.worker.loop import find_pending_test_runs, run_iteration
from app.worker.outbound_processor import OutboundProcessor
from app.worker.test_runner import TestSetRunner


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class _FakeLLM(LLMClient):
    async def complete(self, **_kwargs: Any) -> LLMResponse:
        return LLMResponse(
            text="您好，退貨可於 7 天內申請；請保留發票",
            tool_uses=[],
            stop_reason="end_turn",
            usage=LLMUsage(input_tokens=5, output_tokens=15),
            model="fake",
        )


def _make_processors() -> tuple[DraftProcessor, OutboundProcessor, TestSetRunner]:
    registry = InternalToolRegistry()
    register_builtins(registry)
    loader = SkillLoader(root=_repo_root() / "skills")
    llm = _FakeLLM()
    return (
        DraftProcessor(llm=llm, skill_loader=loader, registry=registry),
        OutboundProcessor(http_client=None),  # type: ignore[arg-type]
        TestSetRunner(llm=llm, skill_loader=loader),
    )


async def _seed_pending_run(session: AsyncSession, *, suffix: str) -> tuple[Tenant, TestRun]:
    tenant = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}-{suffix}")
    session.add(tenant)
    await session.flush()
    await test_set.create_test_case(
        session,
        tenant_id=tenant.id,
        name="退貨",
        user_input="退貨多久",
        expected_outcome="7 天",
        expected_keywords=["7 天", "退貨"],
    )
    run = await test_set.create_test_run(
        session,
        tenant_id=tenant.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )
    return tenant, run


async def test_find_pending_test_runs_returns_pending(
    db_session: AsyncSession,
) -> None:
    _, run = await _seed_pending_run(db_session, suffix="find")
    rows = await find_pending_test_runs(db_session, limit=5)
    assert len(rows) == 1
    assert rows[0].id == run.id


async def test_find_pending_test_runs_excludes_completed(
    db_session: AsyncSession,
) -> None:
    _, run = await _seed_pending_run(db_session, suffix="excl")
    run.status = "completed"
    await db_session.flush()
    rows = await find_pending_test_runs(db_session)
    assert rows == []


async def test_run_iteration_picks_pending_test_run_and_completes(
    db_session: AsyncSession,
) -> None:
    _, run = await _seed_pending_run(db_session, suffix="iter")
    draft, outbound, runner = _make_processors()

    result = await run_iteration(
        db_session,
        draft_processor=draft,
        outbound_processor=outbound,
        test_set_runner=runner,
    )
    assert result.test_runs_processed == 1
    assert result.test_runs_failed == 0
    assert result.did_work is True

    refreshed = (await db_session.execute(select(TestRun).where(TestRun.id == run.id))).scalar_one()
    assert refreshed.status == "completed"
    assert refreshed.pass_rate == 1.0


async def test_run_iteration_without_runner_skips_cycle(
    db_session: AsyncSession,
) -> None:
    """test_set_runner=None → 不撿 pending runs（向後相容）."""
    _, run = await _seed_pending_run(db_session, suffix="norunner")
    draft, outbound, _ = _make_processors()

    result = await run_iteration(
        db_session,
        draft_processor=draft,
        outbound_processor=outbound,
        test_set_runner=None,
    )
    assert result.test_runs_processed == 0

    refreshed = (await db_session.execute(select(TestRun).where(TestRun.id == run.id))).scalar_one()
    assert refreshed.status == "pending"  # 仍是 pending
