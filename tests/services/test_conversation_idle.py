"""Conversation idle timeout service 測試 — 30min cutoff + audit."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog
from app.db.models.conversation import Conversation
from app.db.models.employee import Employee
from app.db.models.tenant import Tenant
from app.services.conversation_idle import close_idle_conversations


async def _seed_conv(
    session: AsyncSession,
    *,
    status: str = "active",
    last_msg_ago: timedelta = timedelta(hours=2),
    suffix: str = "idle",
) -> Conversation:
    tenant = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}-{suffix}")
    session.add(tenant)
    await session.flush()
    emp = Employee(
        tenant_id=tenant.id,
        name="AI",
        role="customer_service",
        status="live",
        version="1.0.0",
    )
    session.add(emp)
    await session.flush()
    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=emp.id,
        employee_version="1.0.0",
        end_user_pseudo_id="u",
        channel="line",
        channel_user_id=f"U-{suffix}",
        status=status,
    )
    session.add(conv)
    await session.flush()
    # 強制設 last_message_at（model 沒 default；我們直接 UPDATE）
    stale = datetime.now(UTC) - last_msg_ago
    await session.execute(
        text("UPDATE conversation SET last_message_at = :t WHERE id = :cid"),
        {"t": stale, "cid": str(conv.id)},
    )
    await session.flush()
    await session.refresh(conv)
    return conv


async def test_closes_idle_active_conversation(db_session: AsyncSession) -> None:
    conv = await _seed_conv(db_session, suffix="closeme")
    result = await close_idle_conversations(db_session)
    assert result.closed_count == 1
    assert str(conv.id) in result.closed_ids

    refreshed = (
        await db_session.execute(select(Conversation).where(Conversation.id == conv.id))
    ).scalar_one()
    assert refreshed.status == "closed"
    assert refreshed.outcome == "abandoned"
    assert refreshed.ended_at is not None

    audit_row = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.event_type == "conversation.idle_closed")
        )
    ).scalar_one()
    assert audit_row.resource_id == str(conv.id)


async def test_does_not_close_recent_conversation(db_session: AsyncSession) -> None:
    """5 分鐘前才聊過的 conversation 不應被關。"""
    conv = await _seed_conv(db_session, last_msg_ago=timedelta(minutes=5), suffix="recent")
    result = await close_idle_conversations(db_session)
    assert result.closed_count == 0

    refreshed = (
        await db_session.execute(select(Conversation).where(Conversation.id == conv.id))
    ).scalar_one()
    assert refreshed.status == "active"


async def test_does_not_close_waiting_human(db_session: AsyncSession) -> None:
    """expert 接手中（waiting_human）不該自動 timeout。"""
    conv = await _seed_conv(db_session, status="waiting_human", suffix="wh")
    result = await close_idle_conversations(db_session)
    assert result.closed_count == 0

    refreshed = (
        await db_session.execute(select(Conversation).where(Conversation.id == conv.id))
    ).scalar_one()
    assert refreshed.status == "waiting_human"


async def test_does_not_close_already_closed(db_session: AsyncSession) -> None:
    conv = await _seed_conv(db_session, status="closed", suffix="cl")
    result = await close_idle_conversations(db_session)
    assert result.closed_count == 0

    refreshed = (
        await db_session.execute(select(Conversation).where(Conversation.id == conv.id))
    ).scalar_one()
    assert refreshed.status == "closed"


async def test_custom_timeout_overrides_default(db_session: AsyncSession) -> None:
    """idle_timeout=5min；conv last_message 10min 前 → 該被關。"""
    conv = await _seed_conv(db_session, last_msg_ago=timedelta(minutes=10), suffix="custom-to")
    result = await close_idle_conversations(db_session, idle_timeout=timedelta(minutes=5))
    assert result.closed_count == 1

    refreshed = (
        await db_session.execute(select(Conversation).where(Conversation.id == conv.id))
    ).scalar_one()
    assert refreshed.status == "closed"


async def test_batch_limit_respected(db_session: AsyncSession) -> None:
    convs = [await _seed_conv(db_session, suffix=f"b-{i}") for i in range(3)]
    result = await close_idle_conversations(db_session, limit=2)
    assert result.closed_count == 2
    assert len(result.closed_ids) == 2
    # 第三個 conv 仍 active
    closed_set = set(result.closed_ids)
    remaining_id = next(c.id for c in convs if str(c.id) not in closed_set)
    refreshed = (
        await db_session.execute(select(Conversation).where(Conversation.id == remaining_id))
    ).scalar_one()
    assert refreshed.status == "active"
