"""Kill switch service 單元測試 — disable / enable / get_state / is_ai_enabled."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog
from app.db.models.tenant import Tenant
from app.services import kill_switch


async def _seed_tenant(session: AsyncSession, suffix: str = "ks") -> Tenant:
    tenant = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}-{suffix}")
    session.add(tenant)
    await session.flush()
    return tenant


async def test_default_state_is_enabled(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, "default")
    state = await kill_switch.get_state(db_session, tenant.id)
    assert state.ai_enabled is True
    assert state.disabled_at is None
    assert state.disabled_by is None


async def test_is_ai_enabled_default_true(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, "isen")
    assert await kill_switch.is_ai_enabled(db_session, tenant.id) is True


async def test_disable_marks_state_and_audits(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, "dis")
    state = await kill_switch.disable_ai(
        db_session,
        tenant_id=tenant.id,
        confirm_tenant_id=tenant.id,
        actor_id="cto",
        reason="incident-2026-05-22: AI hallucinated",
    )
    assert state.ai_enabled is False
    assert state.disabled_by == "cto"
    assert state.disabled_at is not None

    assert await kill_switch.is_ai_enabled(db_session, tenant.id) is False

    audit_row = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.event_type == "kill_switch.disabled")
        )
    ).scalar_one()
    assert audit_row.actor_id == "cto"
    assert "hallucinated" in audit_row.payload["reason"]


async def test_disable_requires_confirm_match(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, "mismatch")
    other = await _seed_tenant(db_session, "other")
    with pytest.raises(kill_switch.KillSwitchError, match="confirm_tenant_id mismatch"):
        await kill_switch.disable_ai(
            db_session,
            tenant_id=tenant.id,
            confirm_tenant_id=other.id,
            actor_id="x",
            reason="r",
        )


async def test_disable_empty_reason_raises(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, "noreason")
    with pytest.raises(kill_switch.KillSwitchError, match="reason cannot be empty"):
        await kill_switch.disable_ai(
            db_session,
            tenant_id=tenant.id,
            confirm_tenant_id=tenant.id,
            actor_id="x",
            reason="   ",
        )


async def test_disable_twice_raises(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, "twice")
    await kill_switch.disable_ai(
        db_session,
        tenant_id=tenant.id,
        confirm_tenant_id=tenant.id,
        actor_id="x",
        reason="first",
    )
    with pytest.raises(kill_switch.KillSwitchError, match="already disabled"):
        await kill_switch.disable_ai(
            db_session,
            tenant_id=tenant.id,
            confirm_tenant_id=tenant.id,
            actor_id="x",
            reason="second",
        )


async def test_enable_restores_state(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, "enable")
    await kill_switch.disable_ai(
        db_session,
        tenant_id=tenant.id,
        confirm_tenant_id=tenant.id,
        actor_id="x",
        reason="r",
    )
    state = await kill_switch.enable_ai(
        db_session,
        tenant_id=tenant.id,
        actor_id="cto",
        reason="incident resolved",
    )
    assert state.ai_enabled is True
    assert state.disabled_at is None
    assert state.disabled_by is None

    audit_row = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.event_type == "kill_switch.enabled")
        )
    ).scalar_one()
    assert audit_row.actor_id == "cto"


async def test_enable_when_already_enabled_raises(
    db_session: AsyncSession,
) -> None:
    tenant = await _seed_tenant(db_session, "alren")
    with pytest.raises(kill_switch.KillSwitchError, match="already enabled"):
        await kill_switch.enable_ai(db_session, tenant_id=tenant.id, actor_id="x", reason="r")
