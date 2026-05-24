"""LINE webhook 端到端測試 — HMAC + dedup + message ingest."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid

from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.webhooks.line import verify_line_signature
from app.db.models.audit_log import AuditLog
from app.db.models.channel_binding import ChannelBinding
from app.db.models.conversation import Conversation
from app.db.models.employee import Employee
from app.db.models.tenant import Tenant
from app.db.models.webhook_event import WebhookEvent

LINE_CHANNEL_ID = "U-line-channel-001"
LINE_SECRET = "test_channel_secret_xxx"


def _sign(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


async def _seed_employee_and_binding(
    session: AsyncSession,
    *,
    channel_id: str = LINE_CHANNEL_ID,
    secret: str = LINE_SECRET,
    enabled: bool = True,
) -> tuple[Tenant, Employee, ChannelBinding]:
    t = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}")
    session.add(t)
    await session.flush()
    e = Employee(
        tenant_id=t.id,
        name="AI CS",
        role="customer_service",
        status="live",
        version="1.0.0",
    )
    session.add(e)
    await session.flush()
    b = ChannelBinding(
        employee_id=e.id,
        channel="line",
        config={"channel_id": channel_id, "channel_secret": secret},
        enabled=enabled,
    )
    session.add(b)
    await session.flush()
    return t, e, b


# ── verify_line_signature unit ──────────────────────


def test_verify_signature_valid() -> None:
    body = b'{"events": []}'
    sig = _sign(body, LINE_SECRET)
    assert verify_line_signature(body, sig, LINE_SECRET) is True


def test_verify_signature_wrong_secret() -> None:
    body = b'{"events": []}'
    sig = _sign(body, "other-secret")
    assert verify_line_signature(body, sig, LINE_SECRET) is False


def test_verify_signature_empty_inputs() -> None:
    assert verify_line_signature(b"x", "", "secret") is False
    assert verify_line_signature(b"x", "sig", "") is False


# ── webhook integration ────────────────────────────


async def test_webhook_unknown_channel_returns_404(
    client: AsyncClient,
    webhook_session: AsyncSession,
) -> None:
    body = b'{"events": []}'
    resp = await client.post(
        "/api/v1/webhooks/line/no-such-channel",
        content=body,
        headers={"X-Line-Signature": _sign(body, LINE_SECRET)},
    )
    assert resp.status_code == 404


async def test_webhook_bad_signature_403_with_audit(
    client: AsyncClient,
    webhook_session: AsyncSession,
) -> None:
    await _seed_employee_and_binding(webhook_session)
    body = b'{"events": []}'
    resp = await client.post(
        f"/api/v1/webhooks/line/{LINE_CHANNEL_ID}",
        content=body,
        headers={"X-Line-Signature": _sign(body, "wrong")},
    )
    assert resp.status_code == 403
    # audit row 應寫入
    audit_row = (
        await webhook_session.execute(
            select(AuditLog).where(AuditLog.event_type == "channel.webhook_signature_failed")
        )
    ).scalar_one()
    assert audit_row.resource_id == LINE_CHANNEL_ID


async def test_webhook_disabled_binding_403(
    client: AsyncClient,
    webhook_session: AsyncSession,
) -> None:
    await _seed_employee_and_binding(webhook_session, enabled=False)
    body = b'{"events": []}'
    resp = await client.post(
        f"/api/v1/webhooks/line/{LINE_CHANNEL_ID}",
        content=body,
        headers={"X-Line-Signature": _sign(body, LINE_SECRET)},
    )
    assert resp.status_code == 403


async def test_webhook_invalid_json_400(
    client: AsyncClient,
    webhook_session: AsyncSession,
) -> None:
    await _seed_employee_and_binding(webhook_session)
    body = b"not json {"
    resp = await client.post(
        f"/api/v1/webhooks/line/{LINE_CHANNEL_ID}",
        content=body,
        headers={"X-Line-Signature": _sign(body, LINE_SECRET)},
    )
    assert resp.status_code == 400


async def test_webhook_message_event_persisted(
    client: AsyncClient,
    webhook_session: AsyncSession,
) -> None:
    tenant, employee, _ = await _seed_employee_and_binding(webhook_session)

    payload = {
        "destination": LINE_CHANNEL_ID,
        "events": [
            {
                "type": "message",
                "webhookEventId": "ev-001",
                "source": {"userId": "U-line-user-aaa", "type": "user"},
                "message": {"type": "text", "id": "m1", "text": "請問退貨期限多久"},
                "timestamp": 1234567890,
            }
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    resp = await client.post(
        f"/api/v1/webhooks/line/{LINE_CHANNEL_ID}",
        content=body,
        headers={"X-Line-Signature": _sign(body, LINE_SECRET)},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["processed"] == 1
    assert data["deduped"] == 0

    # conversation 應建立
    convs = (
        (
            await webhook_session.execute(
                select(Conversation).where(Conversation.tenant_id == tenant.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(convs) == 1
    assert convs[0].channel == "line"
    assert convs[0].channel_user_id == "U-line-user-aaa"
    assert convs[0].employee_id == employee.id
    assert convs[0].message_count == 1
    assert convs[0].status == "active"  # open → active 自動轉

    # message row
    msg_rows = (
        await webhook_session.execute(
            text("SELECT role, content, seq FROM message WHERE conversation_id = :cid"),
            {"cid": str(convs[0].id)},
        )
    ).all()
    assert len(msg_rows) == 1
    assert msg_rows[0][0] == "user"
    assert msg_rows[0][1] == "請問退貨期限多久"
    assert msg_rows[0][2] == 1

    # webhook_event 應有一筆
    we = (
        await webhook_session.execute(select(WebhookEvent).where(WebhookEvent.id == "ev-001"))
    ).scalar_one()
    assert we.channel == "line"


async def test_webhook_dedup_same_event(
    client: AsyncClient,
    webhook_session: AsyncSession,
) -> None:
    await _seed_employee_and_binding(webhook_session)
    payload = {
        "events": [
            {
                "type": "message",
                "webhookEventId": "ev-dup",
                "source": {"userId": "U-x"},
                "message": {"type": "text", "text": "hi"},
            }
        ],
    }
    body = json.dumps(payload).encode()
    sig = _sign(body, LINE_SECRET)

    r1 = await client.post(
        f"/api/v1/webhooks/line/{LINE_CHANNEL_ID}",
        content=body,
        headers={"X-Line-Signature": sig},
    )
    assert r1.status_code == 200
    assert r1.json()["processed"] == 1

    # 重送 → dedup
    r2 = await client.post(
        f"/api/v1/webhooks/line/{LINE_CHANNEL_ID}",
        content=body,
        headers={"X-Line-Signature": sig},
    )
    assert r2.status_code == 200
    assert r2.json()["processed"] == 0
    assert r2.json()["deduped"] == 1


async def test_webhook_non_message_event_skipped(
    client: AsyncClient,
    webhook_session: AsyncSession,
) -> None:
    """follow/unfollow 等 non-message event Phase 1 不處理但 dedup 仍記."""
    await _seed_employee_and_binding(webhook_session)
    payload = {
        "events": [
            {
                "type": "follow",
                "webhookEventId": "ev-follow",
                "source": {"userId": "U-x"},
            }
        ],
    }
    body = json.dumps(payload).encode()
    resp = await client.post(
        f"/api/v1/webhooks/line/{LINE_CHANNEL_ID}",
        content=body,
        headers={"X-Line-Signature": _sign(body, LINE_SECRET)},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["processed"] == 0
    skipped = [e for e in data["events"] if e["type"] == "follow"]
    assert skipped[0]["status"] == "skipped"


async def test_webhook_multiple_messages_continue_same_conversation(
    client: AsyncClient,
    webhook_session: AsyncSession,
) -> None:
    """同 line user 連續兩則訊息應寫到同一個 active conversation."""
    tenant, _, _ = await _seed_employee_and_binding(webhook_session)

    for i, eid in enumerate(["ev-a", "ev-b"], start=1):
        payload = {
            "events": [
                {
                    "type": "message",
                    "webhookEventId": eid,
                    "source": {"userId": "U-same"},
                    "message": {"type": "text", "text": f"msg-{i}"},
                }
            ],
        }
        body = json.dumps(payload).encode()
        resp = await client.post(
            f"/api/v1/webhooks/line/{LINE_CHANNEL_ID}",
            content=body,
            headers={"X-Line-Signature": _sign(body, LINE_SECRET)},
        )
        assert resp.status_code == 200

    convs = (
        (
            await webhook_session.execute(
                select(Conversation).where(Conversation.tenant_id == tenant.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(convs) == 1
    assert convs[0].message_count == 2


async def test_webhook_audit_received(
    client: AsyncClient,
    webhook_session: AsyncSession,
) -> None:
    """成功處理應寫 channel.webhook_received audit."""
    await _seed_employee_and_binding(webhook_session)
    payload = {
        "events": [
            {
                "type": "message",
                "webhookEventId": "ev-audit",
                "source": {"userId": "U-x"},
                "message": {"type": "text", "text": "hi"},
            }
        ]
    }
    body = json.dumps(payload).encode()
    resp = await client.post(
        f"/api/v1/webhooks/line/{LINE_CHANNEL_ID}",
        content=body,
        headers={"X-Line-Signature": _sign(body, LINE_SECRET)},
    )
    assert resp.status_code == 200

    audit_rows = (
        (
            await webhook_session.execute(
                select(AuditLog).where(AuditLog.event_type == "channel.webhook_received")
            )
        )
        .scalars()
        .all()
    )
    assert len(audit_rows) == 1
    assert audit_rows[0].payload["processed"] == 1
    assert audit_rows[0].payload["events_total"] == 1


async def test_webhook_pii_masked_in_stored_message(
    client: AsyncClient,
    webhook_session: AsyncSession,
) -> None:
    """webhook ingress 應 mask PII（email / 手機 / 身分證）後再寫進 message.content."""
    tenant, _, _ = await _seed_employee_and_binding(webhook_session)

    payload = {
        "destination": LINE_CHANNEL_ID,
        "events": [
            {
                "type": "message",
                "webhookEventId": "ev-pii-001",
                "source": {"userId": "U-pii", "type": "user"},
                "message": {
                    "type": "text",
                    "id": "m-pii",
                    "text": "我的 email user@example.com 手機 0912345678",
                },
                "timestamp": 1234567890,
            }
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    resp = await client.post(
        f"/api/v1/webhooks/line/{LINE_CHANNEL_ID}",
        content=body,
        headers={"X-Line-Signature": _sign(body, LINE_SECRET)},
    )
    assert resp.status_code == 200

    # 1) message.content 不應該含 raw PII
    msg_rows = (
        await webhook_session.execute(
            text(
                "SELECT content FROM message WHERE conversation_id IN ("
                " SELECT id FROM conversation WHERE tenant_id = :tid)"
            ),
            {"tid": str(tenant.id)},
        )
    ).all()
    assert len(msg_rows) == 1
    content = msg_rows[0][0]
    assert "user@example.com" not in content
    assert "0912345678" not in content
    assert "[REDACTED:email]" in content
    assert "[REDACTED:tw_mobile]" in content

    # 2) 應有 pii.redacted_in_ingress audit event
    from app.db.models.audit_log import AuditLog

    audit_row = (
        await webhook_session.execute(
            select(AuditLog).where(AuditLog.event_type == "pii.redacted_in_ingress")
        )
    ).scalar_one()
    assert audit_row.payload["total"] == 2
    assert audit_row.payload["redactions"] == {"email": 1, "tw_mobile": 1}
