"""OncallSchedule schema tests — Phase 1 後續 #17 (DB 25/25)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.oncall_schedule import OncallSchedule
from app.db.models.tenant import Tenant


async def _make_tenant(session: AsyncSession, slug: str) -> Tenant:
    t = Tenant(name=f"T-{slug}", slug=slug)
    session.add(t)
    await session.flush()
    return t


async def test_oncall_create(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "oncall-1")
    now = datetime.now(UTC)
    sched = OncallSchedule(
        tenant_id=tenant.id,
        shift_start=now,
        shift_end=now + timedelta(hours=8),
        primary_expert_id=uuid.uuid4(),
        notes="weekly Monday day shift",
    )
    db_session.add(sched)
    await db_session.flush()
    assert sched.id is not None
    assert sched.secondary_expert_id is None
    assert sched.pagerduty_schedule_id is None


async def test_oncall_time_range_check(db_session: AsyncSession) -> None:
    """shift_end <= shift_start → CHECK 阻擋。"""
    tenant = await _make_tenant(db_session, "oncall-bad")
    now = datetime.now(UTC)
    bad = OncallSchedule(
        tenant_id=tenant.id,
        shift_start=now,
        shift_end=now - timedelta(hours=1),  # invalid
    )
    db_session.add(bad)
    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()
    assert "time_range" in str(exc.value).lower()


async def test_oncall_null_experts_allowed(db_session: AsyncSession) -> None:
    """primary / secondary 可全 NULL（無人值班 fallback default channel）。"""
    tenant = await _make_tenant(db_session, "oncall-null")
    now = datetime.now(UTC)
    sched = OncallSchedule(
        tenant_id=tenant.id,
        shift_start=now,
        shift_end=now + timedelta(hours=12),
    )
    db_session.add(sched)
    await db_session.flush()
    assert sched.primary_expert_id is None
    assert sched.secondary_expert_id is None


async def test_oncall_query_by_time_range(db_session: AsyncSession) -> None:
    """idx_oncall_schedule_tenant_shift 支援『此時刻誰值班』查詢。"""
    tenant = await _make_tenant(db_session, "oncall-q")
    now = datetime.now(UTC)
    morning = OncallSchedule(
        tenant_id=tenant.id,
        shift_start=now,
        shift_end=now + timedelta(hours=8),
        primary_expert_id=uuid.uuid4(),
    )
    evening = OncallSchedule(
        tenant_id=tenant.id,
        shift_start=now + timedelta(hours=8),
        shift_end=now + timedelta(hours=16),
        primary_expert_id=uuid.uuid4(),
    )
    db_session.add_all([morning, evening])
    await db_session.flush()

    # query: 此刻誰值班
    check_time = now + timedelta(hours=2)
    result = (
        await db_session.execute(
            select(OncallSchedule).where(
                OncallSchedule.tenant_id == tenant.id,
                OncallSchedule.shift_start <= check_time,
                OncallSchedule.shift_end > check_time,
            )
        )
    ).scalar_one()
    assert result.id == morning.id


async def test_oncall_rls_enabled(db_session: AsyncSession) -> None:
    """RLS enabled on oncall_schedule (SEC §6.1 #4)."""
    result = (
        await db_session.execute(
            text("SELECT relrowsecurity FROM pg_class " "WHERE relname='oncall_schedule'")
        )
    ).scalar_one()
    assert result is True
