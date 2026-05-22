"""MC-011 Channel Gateway 測試 — channel_binding / webhook_event / outbound_message."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.channel_binding import ChannelBinding
from app.db.models.employee import Employee
from app.db.models.outbound_message import OutboundMessage
from app.db.models.tenant import Tenant
from app.db.models.webhook_event import WebhookEvent


async def _make_tenant(session: AsyncSession, slug: str) -> Tenant:
    t = Tenant(name=f"T-{slug}", slug=slug)
    session.add(t)
    await session.flush()
    return t


async def _make_employee(session: AsyncSession, tenant: Tenant) -> Employee:
    e = Employee(
        tenant_id=tenant.id,
        name="AI 客服",
        role="customer_service",
        status="draft",
        version="1.0.0",
    )
    session.add(e)
    await session.flush()
    return e


# ── ChannelBinding ──────────────────────────────────


async def test_channel_binding_create(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "cb-create")
    emp = await _make_employee(db_session, tenant)
    binding = ChannelBinding(
        employee_id=emp.id,
        channel="line",
        config={"channel_id": "U-line-id", "channel_secret_ref": "secret://line/1"},
    )
    db_session.add(binding)
    await db_session.flush()

    assert binding.id is not None
    assert binding.enabled is True
    assert binding.config["channel_id"] == "U-line-id"


async def test_channel_binding_channel_check(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "cb-bad-chan")
    emp = await _make_employee(db_session, tenant)
    binding = ChannelBinding(
        employee_id=emp.id,
        channel="wechat",  # 不在允許清單
    )
    db_session.add(binding)
    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()
    assert "channel_check" in str(exc.value).lower()


async def test_channel_binding_unique_emp_channel(db_session: AsyncSession) -> None:
    """同 employee 不可重複綁同個 channel."""
    tenant = await _make_tenant(db_session, "cb-uniq")
    emp = await _make_employee(db_session, tenant)
    db_session.add(ChannelBinding(employee_id=emp.id, channel="line"))
    await db_session.flush()
    db_session.add(ChannelBinding(employee_id=emp.id, channel="line"))
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_channel_binding_disabled(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "cb-disabled")
    emp = await _make_employee(db_session, tenant)
    binding = ChannelBinding(
        employee_id=emp.id,
        channel="line",
        enabled=False,
    )
    db_session.add(binding)
    await db_session.flush()
    assert binding.enabled is False


# ── WebhookEvent ───────────────────────────────────


async def test_webhook_event_dedup_via_pk(db_session: AsyncSession) -> None:
    """同 (id, channel) 不可重複 — webhook 進來 INSERT 阻擋即代表 dedup 命中."""
    db_session.add(WebhookEvent(id="line-event-123", channel="line"))
    await db_session.flush()

    db_session.add(WebhookEvent(id="line-event-123", channel="line"))
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_webhook_event_different_channels_ok(db_session: AsyncSession) -> None:
    """同 id 不同 channel 可共存（不同 webhook 來源可能撞 id）."""
    db_session.add(WebhookEvent(id="ev-abc", channel="line"))
    db_session.add(WebhookEvent(id="ev-abc", channel="whatsapp"))
    await db_session.flush()  # no error


# ── OutboundMessage ────────────────────────────────


async def test_outbound_message_pending(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "om-pending")
    emp = await _make_employee(db_session, tenant)

    # 先建一個 conversation 滿足 FK
    from app.db.models.conversation import Conversation

    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=emp.id,
        employee_version="1.0.0",
        end_user_pseudo_id="u",
        channel="line",
        channel_user_id="u",
    )
    db_session.add(conv)
    await db_session.flush()

    out = OutboundMessage(
        tenant_id=tenant.id,
        conversation_id=conv.id,
        message_id=uuid.uuid4(),  # logical FK
        channel="line",
        channel_user_id="u-hash",
        status="pending",
    )
    db_session.add(out)
    await db_session.flush()

    assert out.id is not None
    assert out.retry_count == 0
    assert out.sent_at is None


async def test_outbound_status_check(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "om-bad-status")
    emp = await _make_employee(db_session, tenant)
    from app.db.models.conversation import Conversation

    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=emp.id,
        employee_version="1.0.0",
        end_user_pseudo_id="u",
        channel="line",
        channel_user_id="u",
    )
    db_session.add(conv)
    await db_session.flush()

    out = OutboundMessage(
        tenant_id=tenant.id,
        conversation_id=conv.id,
        message_id=uuid.uuid4(),
        channel="line",
        channel_user_id="u",
        status="weird",
    )
    db_session.add(out)
    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()
    assert "status_check" in str(exc.value).lower()


# ── RLS ─────────────────────────────────────────────


async def test_mc011_rls_policies_exist(db_session: AsyncSession) -> None:
    result = await db_session.execute(
        text(
            "SELECT tablename, policyname FROM pg_policies "
            "WHERE schemaname='public' "
            "AND tablename IN ('channel_binding', 'webhook_event', 'outbound_message')"
        )
    )
    policies = {(row[0], row[1]) for row in result.all()}
    assert ("channel_binding", "channel_binding_allow_all") in policies
    assert ("webhook_event", "webhook_event_allow_all") in policies
    assert ("outbound_message", "outbound_message_tenant_isolation") in policies


async def test_outbound_partial_index_exists(db_session: AsyncSession) -> None:
    result = await db_session.execute(
        text(
            "SELECT indexdef FROM pg_indexes "
            "WHERE schemaname='public' AND indexname='idx_outbound_pending'"
        )
    )
    indexdef = result.scalar_one_or_none()
    assert indexdef is not None
    # partial index 條件應出現在 indexdef
    assert "pending" in indexdef.lower() and "retrying" in indexdef.lower()


# ── Cascade delete ──────────────────────────────────


async def test_channel_binding_cascade_on_employee_delete(
    db_session: AsyncSession,
) -> None:
    tenant = await _make_tenant(db_session, "cb-cascade")
    emp = await _make_employee(db_session, tenant)
    db_session.add(ChannelBinding(employee_id=emp.id, channel="line"))
    await db_session.flush()

    # 刪 employee 應 CASCADE 刪 channel_binding
    await db_session.delete(emp)
    await db_session.flush()

    bindings = (await db_session.execute(select(ChannelBinding))).scalars().all()
    assert bindings == []
