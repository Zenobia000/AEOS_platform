"""TestSet service tests — case CRUD + run lifecycle."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog
from app.db.models.tenant import Tenant
from app.db.models.test_case import TestCase
from app.db.models.test_run import TestRun
from app.db.models.test_run_case import TestRunCase
from app.services import test_set


async def _seed_tenant(session: AsyncSession, suffix: str = "ts") -> Tenant:
    t = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}-{suffix}")
    session.add(t)
    await session.flush()
    return t


async def test_create_test_case_returns_persisted_row(
    db_session: AsyncSession,
) -> None:
    t = await _seed_tenant(db_session, "create")
    tc = await test_set.create_test_case(
        db_session,
        tenant_id=t.id,
        name="退貨期限",
        user_input="請問退貨多久",
        expected_outcome="回答 7 天 + 須保留發票",
        expected_keywords=["7 天", "發票"],
        created_by="expert-amy",
    )
    refreshed = (
        await db_session.execute(select(TestCase).where(TestCase.id == tc.id))
    ).scalar_one()
    assert refreshed.name == "退貨期限"
    assert refreshed.created_by == "expert-amy"
    assert refreshed.enabled is True
    assert list(refreshed.expected_keywords) == ["7 天", "發票"]


async def test_create_test_case_validation_errors(
    db_session: AsyncSession,
) -> None:
    t = await _seed_tenant(db_session, "val")
    with pytest.raises(test_set.TestSetError, match="name"):
        await test_set.create_test_case(
            db_session,
            tenant_id=t.id,
            name="   ",
            user_input="x",
            expected_outcome="y",
        )
    with pytest.raises(test_set.TestSetError, match="user_input"):
        await test_set.create_test_case(
            db_session,
            tenant_id=t.id,
            name="a",
            user_input="  ",
            expected_outcome="y",
        )
    with pytest.raises(test_set.TestSetError, match="expected_outcome"):
        await test_set.create_test_case(
            db_session,
            tenant_id=t.id,
            name="a",
            user_input="x",
            expected_outcome="",
        )


async def test_list_test_cases_filters_disabled(
    db_session: AsyncSession,
) -> None:
    t = await _seed_tenant(db_session, "list")
    tc1 = await test_set.create_test_case(
        db_session,
        tenant_id=t.id,
        name="a",
        user_input="x",
        expected_outcome="y",
    )
    tc2 = await test_set.create_test_case(
        db_session,
        tenant_id=t.id,
        name="b",
        user_input="x",
        expected_outcome="y",
    )
    await test_set.disable_test_case(db_session, test_case_id=tc2.id)

    enabled = await test_set.list_test_cases(db_session, tenant_id=t.id)
    assert {c.id for c in enabled} == {tc1.id}

    all_cases = await test_set.list_test_cases(db_session, tenant_id=t.id, enabled_only=False)
    assert {c.id for c in all_cases} == {tc1.id, tc2.id}


async def test_create_test_run_seeds_run_case_rows(
    db_session: AsyncSession,
) -> None:
    t = await _seed_tenant(db_session, "run-seed")
    for i in range(3):
        await test_set.create_test_case(
            db_session,
            tenant_id=t.id,
            name=f"case-{i}",
            user_input="x",
            expected_outcome="y",
        )

    run = await test_set.create_test_run(
        db_session,
        tenant_id=t.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
        created_by="cto",
    )
    assert run.status == "pending"
    assert run.total_cases == 3

    cases_in_run = (
        (await db_session.execute(select(TestRunCase).where(TestRunCase.test_run_id == run.id)))
        .scalars()
        .all()
    )
    assert len(list(cases_in_run)) == 3

    audit_row = (
        await db_session.execute(select(AuditLog).where(AuditLog.event_type == "test_run.created"))
    ).scalar_one()
    assert audit_row.payload["total_cases"] == 3


async def test_create_run_without_cases_raises(
    db_session: AsyncSession,
) -> None:
    t = await _seed_tenant(db_session, "empty")
    with pytest.raises(test_set.TestSetError, match="no enabled test_case"):
        await test_set.create_test_run(
            db_session,
            tenant_id=t.id,
            skill_slug="any",
            skill_version="any",
        )


async def test_mark_run_running_transitions(db_session: AsyncSession) -> None:
    t = await _seed_tenant(db_session, "running")
    await test_set.create_test_case(
        db_session, tenant_id=t.id, name="a", user_input="x", expected_outcome="y"
    )
    run = await test_set.create_test_run(
        db_session,
        tenant_id=t.id,
        skill_slug="s",
        skill_version="v",
    )
    refreshed = await test_set.mark_run_running(db_session, run_id=run.id)
    assert refreshed.status == "running"
    assert refreshed.started_at is not None


async def test_mark_running_when_not_pending_raises(
    db_session: AsyncSession,
) -> None:
    t = await _seed_tenant(db_session, "notpending")
    await test_set.create_test_case(
        db_session, tenant_id=t.id, name="a", user_input="x", expected_outcome="y"
    )
    run = await test_set.create_test_run(
        db_session, tenant_id=t.id, skill_slug="s", skill_version="v"
    )
    await test_set.mark_run_running(db_session, run_id=run.id)
    with pytest.raises(test_set.TestSetError, match="not in pending"):
        await test_set.mark_run_running(db_session, run_id=run.id)


async def test_finalize_run_aggregates_correctly(
    db_session: AsyncSession,
) -> None:
    t = await _seed_tenant(db_session, "final")
    cases = []
    for i in range(4):
        tc = await test_set.create_test_case(
            db_session,
            tenant_id=t.id,
            name=f"c-{i}",
            user_input="x",
            expected_outcome="y",
        )
        cases.append(tc)
    run = await test_set.create_test_run(
        db_session, tenant_id=t.id, skill_slug="s", skill_version="v"
    )

    # 直接更新 test_run_case 模擬 runner 結果（3 passed + 1 failed）
    trcs = (
        (await db_session.execute(select(TestRunCase).where(TestRunCase.test_run_id == run.id)))
        .scalars()
        .all()
    )
    statuses = ["passed", "passed", "passed", "failed"]
    for trc, st in zip(trcs, statuses, strict=True):
        trc.status = st
    await db_session.flush()

    summary = await test_set.finalize_run(db_session, run_id=run.id)
    assert summary.passed_cases == 3
    assert summary.failed_cases == 1
    assert summary.pass_rate == 0.75
    assert summary.status == "completed"

    refreshed = (await db_session.execute(select(TestRun).where(TestRun.id == run.id))).scalar_one()
    assert refreshed.passed_cases == 3
    assert refreshed.completed_at is not None
