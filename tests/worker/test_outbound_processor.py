"""OutboundProcessor 行為測試 — LINE Push API mock + retry / fail."""

from __future__ import annotations

import uuid

import httpx
import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog
from app.db.models.channel_binding import ChannelBinding
from app.db.models.conversation import Conversation
from app.db.models.employee import Employee
from app.db.models.outbound_message import OutboundMessage
from app.db.models.tenant import Tenant
from app.worker.outbound_processor import OutboundProcessor

LINE_TOKEN = "channel-access-token-fake"


async def _seed_outbound(
    session: AsyncSession,
    *,
    text_content: str = "您好，有什麼可以幫您？",
    retry_count: int = 0,
    enabled_binding: bool = True,
    set_token: bool = True,
) -> tuple[Tenant, Conversation, OutboundMessage, uuid.UUID]:
    """建出一條完整鏈：tenant → employee → channel_binding → conversation → message → outbound."""
    tenant = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}")
    session.add(tenant)
    await session.flush()
    employee = Employee(
        tenant_id=tenant.id,
        name="AI CS",
        role="customer_service",
        status="live",
        version="1.0.0",
    )
    session.add(employee)
    await session.flush()
    config: dict[str, str] = {"channel_id": "U-line-1"}
    if set_token:
        config["channel_access_token"] = LINE_TOKEN
    session.add(
        ChannelBinding(
            employee_id=employee.id,
            channel="line",
            config=config,
            enabled=enabled_binding,
        )
    )
    await session.flush()
    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=employee.id,
        employee_version="1.0.0",
        end_user_pseudo_id="u-pseudo",
        channel="line",
        channel_user_id="U-end-user-1",
    )
    session.add(conv)
    await session.flush()

    # 寫一則 assistant message + 拿 id
    row = (
        await session.execute(
            text(
                "INSERT INTO message "
                "(id, conversation_id, seq, role, content, created_at) "
                "VALUES (gen_random_uuid(), :cid, 1, 'assistant', :c, NOW()) "
                "RETURNING id"
            ),
            {"cid": str(conv.id), "c": text_content},
        )
    ).first()
    msg_id = uuid.UUID(str(row[0]))  # type: ignore[index]

    out = OutboundMessage(
        tenant_id=tenant.id,
        conversation_id=conv.id,
        message_id=msg_id,
        channel="line",
        channel_user_id="U-end-user-1",
        status="pending",
        retry_count=retry_count,
    )
    session.add(out)
    await session.flush()
    return tenant, conv, out, msg_id


# ── happy path ──────────────────────────────────────


async def test_push_success_marks_sent(db_session: AsyncSession) -> None:
    _, _, out, _ = await _seed_outbound(db_session)

    captured_headers: dict[str, str] = {}
    captured_url: list[str] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        captured_url.append(str(request.url))
        captured_headers.update(dict(request.headers))
        return httpx.Response(200, json={})

    transport = httpx.MockTransport(_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        processor = OutboundProcessor(http_client=client)
        result = await processor.process_one(db_session, out)

    assert result.status == "sent"
    assert result.http_status == 200
    assert captured_url[0] == "https://api.line.me/v2/bot/message/push"
    assert captured_headers["authorization"] == f"Bearer {LINE_TOKEN}"

    # DB row updated
    refreshed = (
        await db_session.execute(select(OutboundMessage).where(OutboundMessage.id == out.id))
    ).scalar_one()
    assert refreshed.status == "sent"
    assert refreshed.sent_at is not None
    assert refreshed.error_message is None

    # audit channel.message_pushed
    audit_row = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.event_type == "channel.message_pushed")
        )
    ).scalar_one()
    assert audit_row.resource_id == str(out.id)


# ── transient errors → retrying ─────────────────────


@pytest.mark.parametrize("http_status", [429, 500, 502, 503])
async def test_transient_status_marks_retrying(
    db_session: AsyncSession,
    http_status: int,
) -> None:
    _, _, out, _ = await _seed_outbound(db_session)
    transport = httpx.MockTransport(lambda _req: httpx.Response(http_status, text="boom"))
    async with httpx.AsyncClient(transport=transport) as client:
        processor = OutboundProcessor(http_client=client, max_retries=3)
        result = await processor.process_one(db_session, out)

    assert result.status == "retrying"
    assert result.http_status == http_status

    refreshed = (
        await db_session.execute(select(OutboundMessage).where(OutboundMessage.id == out.id))
    ).scalar_one()
    assert refreshed.status == "retrying"
    assert refreshed.retry_count == 1
    assert refreshed.error_message is not None and str(http_status) in refreshed.error_message


# ── max_retries exceeded → failed ───────────────────


async def test_max_retries_exceeded_fails(db_session: AsyncSession) -> None:
    """retry_count=2 + max_retries=3 → 下次失敗即 failed."""
    _, _, out, _ = await _seed_outbound(db_session, retry_count=2)
    transport = httpx.MockTransport(lambda _req: httpx.Response(500))
    async with httpx.AsyncClient(transport=transport) as client:
        processor = OutboundProcessor(http_client=client, max_retries=3)
        result = await processor.process_one(db_session, out)

    assert result.status == "failed"
    refreshed = (
        await db_session.execute(select(OutboundMessage).where(OutboundMessage.id == out.id))
    ).scalar_one()
    assert refreshed.status == "failed"
    assert refreshed.retry_count == 3

    audit_row = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.event_type == "channel.message_push_failed")
        )
    ).scalar_one()
    assert "max_retries" in audit_row.payload["error_excerpt"]


# ── 4xx 永久錯誤 → failed（不重試）────────────────


@pytest.mark.parametrize("http_status", [400, 401, 403, 404])
async def test_permanent_4xx_fails_immediately(
    db_session: AsyncSession,
    http_status: int,
) -> None:
    _, _, out, _ = await _seed_outbound(db_session)
    transport = httpx.MockTransport(lambda _req: httpx.Response(http_status, json={"error": "x"}))
    async with httpx.AsyncClient(transport=transport) as client:
        processor = OutboundProcessor(http_client=client)
        result = await processor.process_one(db_session, out)

    assert result.status == "failed"
    assert result.http_status == http_status
    refreshed = (
        await db_session.execute(select(OutboundMessage).where(OutboundMessage.id == out.id))
    ).scalar_one()
    assert refreshed.status == "failed"
    assert refreshed.retry_count == 0  # 沒進 retry，直接 failed


# ── timeout → retrying ──────────────────────────────


async def test_timeout_marks_retrying(db_session: AsyncSession) -> None:
    _, _, out, _ = await _seed_outbound(db_session)

    def _handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("read timeout", request=request)

    transport = httpx.MockTransport(_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        processor = OutboundProcessor(http_client=client)
        result = await processor.process_one(db_session, out)

    assert result.status == "retrying"
    assert result.http_status is None
    refreshed = (
        await db_session.execute(select(OutboundMessage).where(OutboundMessage.id == out.id))
    ).scalar_one()
    assert "timeout" in (refreshed.error_message or "").lower()


# ── missing message content → fail permanent ────────


async def test_missing_message_content_fails(db_session: AsyncSession) -> None:
    """outbound.message_id 對不到 message → 立刻 failed."""
    _, _, out, _ = await _seed_outbound(db_session)
    # 把 outbound.message_id 換成一個不存在的 UUID
    bogus = uuid.uuid4()
    await db_session.execute(
        text("UPDATE outbound_message SET message_id = :mid WHERE id = :oid"),
        {"mid": str(bogus), "oid": str(out.id)},
    )
    await db_session.refresh(out)

    transport = httpx.MockTransport(lambda _req: httpx.Response(200))
    async with httpx.AsyncClient(transport=transport) as client:
        processor = OutboundProcessor(http_client=client)
        result = await processor.process_one(db_session, out)

    assert result.status == "failed"
    assert "message" in (result.error or "")
    assert "not found" in (result.error or "")


# ── missing channel_access_token → fail permanent ───


async def test_missing_token_fails(db_session: AsyncSession) -> None:
    _, _, out, _ = await _seed_outbound(db_session, set_token=False)
    transport = httpx.MockTransport(lambda _req: httpx.Response(200))
    async with httpx.AsyncClient(transport=transport) as client:
        processor = OutboundProcessor(http_client=client)
        result = await processor.process_one(db_session, out)

    assert result.status == "failed"
    assert "channel_access_token" in (result.error or "")


# ── unsupported channel → fail permanent ────────────


async def test_unsupported_channel_fails(db_session: AsyncSession) -> None:
    # 直接改 channel 欄位（繞過 CHECK）— 在 PG 端會被擋；改用其他 channel:
    # 寫一筆全新 web_chat outbound
    tenant = Tenant(name="X", slug=f"x-{uuid.uuid4().hex[:6]}")
    db_session.add(tenant)
    await db_session.flush()
    emp = Employee(
        tenant_id=tenant.id,
        name="x",
        role="customer_service",
        status="live",
        version="1.0.0",
    )
    db_session.add(emp)
    await db_session.flush()
    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=emp.id,
        employee_version="1.0.0",
        end_user_pseudo_id="x",
        channel="web_chat",
        channel_user_id="x",
    )
    db_session.add(conv)
    await db_session.flush()
    other = OutboundMessage(
        tenant_id=tenant.id,
        conversation_id=conv.id,
        message_id=uuid.uuid4(),
        channel="web_chat",
        channel_user_id="x",
        status="pending",
    )
    db_session.add(other)
    await db_session.flush()

    transport = httpx.MockTransport(lambda _req: httpx.Response(200))
    async with httpx.AsyncClient(transport=transport) as client:
        processor = OutboundProcessor(http_client=client)
        result = await processor.process_one(db_session, other)

    assert result.status == "failed"
    assert "unsupported channel" in (result.error or "")


# ── disabled binding ─────────────────────────────────


async def test_disabled_binding_no_token(db_session: AsyncSession) -> None:
    """channel_binding.enabled=False → load_channel_token 找不到 → failed."""
    _, _, out, _ = await _seed_outbound(db_session, enabled_binding=False)
    transport = httpx.MockTransport(lambda _req: httpx.Response(200))
    async with httpx.AsyncClient(transport=transport) as client:
        processor = OutboundProcessor(http_client=client)
        result = await processor.process_one(db_session, out)
    assert result.status == "failed"
