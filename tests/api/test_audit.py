"""Audit Browse API integration tests."""

from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.conversation import Conversation
from app.db.models.employee import Employee
from app.db.models.outbound_message import OutboundMessage
from app.db.models.tenant import Tenant
from app.services import audit as audit_svc


async def _seed_conv_with_audit(
    session: AsyncSession, *, suffix: str
) -> tuple[Tenant, Conversation, OutboundMessage, uuid.UUID]:
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
        status="active",
    )
    session.add(conv)
    await session.flush()

    # 寫 user + assistant 兩則 message
    msg_row = (
        await session.execute(
            text(
                "INSERT INTO message (id, conversation_id, seq, role, content, "
                "created_at) VALUES (gen_random_uuid(), :cid, 1, 'user', "
                "'退貨多久', NOW()) RETURNING id"
            ),
            {"cid": str(conv.id)},
        )
    ).first()
    await session.execute(
        text(
            "INSERT INTO message (id, conversation_id, seq, role, content, "
            "created_at) VALUES (gen_random_uuid(), :cid, 2, 'assistant', "
            "'7 天內可退', NOW())"
        ),
        {"cid": str(conv.id)},
    )
    msg_id = uuid.UUID(str(msg_row[0]))  # type: ignore[index]
    await session.execute(
        text("UPDATE conversation SET message_count = 2 WHERE id = :cid"),
        {"cid": str(conv.id)},
    )

    out = OutboundMessage(
        tenant_id=tenant.id,
        conversation_id=conv.id,
        message_id=msg_id,
        channel="line",
        channel_user_id=conv.channel_user_id,
        status="sent",
    )
    session.add(out)
    await session.flush()

    # 撒一些 audit
    await audit_svc.emit(
        session,
        event_type="expert.draft_approved",
        tenant_id=tenant.id,
        actor_id="expert-amy",
        resource_type="outbound_message",
        resource_id=str(out.id),
        payload={"channel": "line"},
    )
    await audit_svc.emit(
        session,
        event_type="channel.message_pushed",
        tenant_id=tenant.id,
        actor_id="outbound_worker",
        resource_type="outbound_message",
        resource_id=str(out.id),
        payload={"channel": "line"},
    )
    return tenant, conv, out, msg_id


async def test_list_events_returns_audit_rows(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    tenant, _, _, _ = await _seed_conv_with_audit(webhook_session, suffix="ev")
    resp = await client.get(f"/api/v1/audit/events?tenant_id={tenant.id}&since_hours=1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 2
    types = {e["event_type"] for e in body["items"]}
    assert "expert.draft_approved" in types
    assert "channel.message_pushed" in types


async def test_list_events_filter_by_event_type(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    tenant, _, _, _ = await _seed_conv_with_audit(webhook_session, suffix="ft")
    resp = await client.get(
        f"/api/v1/audit/events?tenant_id={tenant.id}&event_type=expert.draft_approved"
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(e["event_type"] == "expert.draft_approved" for e in items)


async def test_list_conversations(client: AsyncClient, webhook_session: AsyncSession) -> None:
    tenant, conv, _, _ = await _seed_conv_with_audit(webhook_session, suffix="lc")
    resp = await client.get(f"/api/v1/audit/conversations?tenant_id={tenant.id}")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(c["conversation_id"] == str(conv.id) for c in items)


async def test_conversation_detail_returns_full_timeline(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    _, conv, out, _ = await _seed_conv_with_audit(webhook_session, suffix="dt")
    resp = await client.get(f"/api/v1/audit/conversations/{conv.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["conversation"]["id"] == str(conv.id)
    assert len(body["messages"]) == 2
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][1]["role"] == "assistant"
    assert len(body["outbounds"]) == 1
    assert body["outbounds"][0]["id"] == str(out.id)
    assert len(body["audit_events"]) >= 2

    types = {e["event_type"] for e in body["audit_events"]}
    assert "expert.draft_approved" in types
    assert "channel.message_pushed" in types


async def test_conversation_detail_404(client: AsyncClient, webhook_session: AsyncSession) -> None:
    resp = await client.get(f"/api/v1/audit/conversations/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── Phase 1 後續 #4: audit filter + #5: conversation export ──


async def test_audit_filter_by_resource_type(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    tenant, _, _, _ = await _seed_conv_with_audit(webhook_session, suffix="rt")
    resp = await client.get(
        f"/api/v1/audit/events?tenant_id={tenant.id}&resource_type=outbound_message"
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(it["resource_type"] == "outbound_message" for it in items)
    assert len(items) >= 1


async def test_audit_filter_by_actor_id(client: AsyncClient, webhook_session: AsyncSession) -> None:
    tenant, _, _, _ = await _seed_conv_with_audit(webhook_session, suffix="ai")
    resp = await client.get(f"/api/v1/audit/events?tenant_id={tenant.id}&actor_id=outbound_worker")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(it["actor_id"] == "outbound_worker" for it in items)


async def test_conversation_export(client: AsyncClient, webhook_session: AsyncSession) -> None:
    tenant, conv, _, _ = await _seed_conv_with_audit(webhook_session, suffix="export")
    resp = await client.get(f"/api/v1/audit/conversations/{conv.id}/export")
    assert resp.status_code == 200
    body = resp.json()
    assert body["schema_version"] == "1.0"
    assert body["conversation"]["id"] == str(conv.id)
    assert body["conversation"]["tenant_id"] == str(tenant.id)
    assert "messages" in body
    assert "outbound_messages" in body
    assert "audit_events" in body
    assert len(body["audit_events"]) >= 2  # draft_approved + message_pushed


async def test_conversation_export_404(client: AsyncClient, webhook_session: AsyncSession) -> None:
    resp = await client.get(f"/api/v1/audit/conversations/{uuid.uuid4()}/export")
    assert resp.status_code == 404
