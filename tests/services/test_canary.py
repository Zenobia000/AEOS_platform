"""Canary service tests — bucket / get / set / decide_outbound_status."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog
from app.db.models.tenant import Tenant
from app.services import canary
from app.services.canary import decide_outbound_status


async def _seed_tenant(session: AsyncSession, suffix: str = "cn") -> Tenant:
    t = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}-{suffix}")
    session.add(t)
    await session.flush()
    return t


def test_decide_zero_always_awaiting_review() -> None:
    for _ in range(20):
        assert (
            decide_outbound_status(conversation_id=uuid.uuid4(), canary_percent=0)
            == "awaiting_review"
        )


def test_decide_100_always_pending() -> None:
    for _ in range(20):
        assert decide_outbound_status(conversation_id=uuid.uuid4(), canary_percent=100) == "pending"


def test_decide_50_roughly_balanced() -> None:
    """50% — 100 random UUIDs，落 pending 比例應在 30~70% 區間（弱保證）."""
    pending = sum(
        decide_outbound_status(conversation_id=uuid.uuid4(), canary_percent=50) == "pending"
        for _ in range(200)
    )
    assert 60 <= pending <= 140  # 50% ± 20pp，1000 樣本以上會更收斂


def test_decide_deterministic_per_conversation() -> None:
    """同 conversation_id + 同 percent → 永遠同 bucket."""
    conv = uuid.uuid4()
    first = decide_outbound_status(conversation_id=conv, canary_percent=37)
    for _ in range(10):
        assert decide_outbound_status(conversation_id=conv, canary_percent=37) == first


async def test_get_default_zero(db_session: AsyncSession) -> None:
    t = await _seed_tenant(db_session, "default")
    assert await canary.get_canary_percent(db_session, tenant_id=t.id) == 0


async def test_set_then_get(db_session: AsyncSession) -> None:
    t = await _seed_tenant(db_session, "set")
    state = await canary.set_canary_percent(
        db_session,
        tenant_id=t.id,
        percent=25,
        actor_id="cto",
        reason="pass rate 0.85, raise to 25%",
    )
    assert state.canary_percent == 25
    assert await canary.get_canary_percent(db_session, tenant_id=t.id) == 25

    audit_row = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.event_type == "canary.percent_changed")
        )
    ).scalar_one()
    assert audit_row.payload["old_percent"] == 0
    assert audit_row.payload["new_percent"] == 25
    assert audit_row.actor_id == "cto"


async def test_set_out_of_range_raises(db_session: AsyncSession) -> None:
    t = await _seed_tenant(db_session, "oor")
    with pytest.raises(canary.CanaryError, match="0-100"):
        await canary.set_canary_percent(
            db_session,
            tenant_id=t.id,
            percent=150,
            actor_id="x",
            reason="r",
        )
    with pytest.raises(canary.CanaryError, match="0-100"):
        await canary.set_canary_percent(
            db_session,
            tenant_id=t.id,
            percent=-1,
            actor_id="x",
            reason="r",
        )


async def test_set_empty_reason_raises(db_session: AsyncSession) -> None:
    t = await _seed_tenant(db_session, "noreason")
    with pytest.raises(canary.CanaryError, match="reason"):
        await canary.set_canary_percent(
            db_session,
            tenant_id=t.id,
            percent=10,
            actor_id="x",
            reason="   ",
        )


async def test_set_same_value_raises(db_session: AsyncSession) -> None:
    t = await _seed_tenant(db_session, "same")
    await canary.set_canary_percent(
        db_session, tenant_id=t.id, percent=20, actor_id="x", reason="r"
    )
    with pytest.raises(canary.CanaryError, match="no change"):
        await canary.set_canary_percent(
            db_session,
            tenant_id=t.id,
            percent=20,
            actor_id="x",
            reason="r2",
        )
