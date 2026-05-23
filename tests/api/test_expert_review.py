"""Expert Console HTTP API integration tests — list / approve / edit / reject."""

from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.conversation import Conversation
from app.db.models.employee import Employee
from app.db.models.outbound_message import OutboundMessage
from app.db.models.tenant import Tenant


async def _seed_awaiting_review(
    session: AsyncSession,
    *,
    draft_text: str = "您好，本店退貨期限為到貨後 7 天內",
    slug_suffix: str = "exp",
) -> tuple[Tenant, OutboundMessage, uuid.UUID]:
    tenant = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}-{slug_suffix}")
    session.add(tenant)
    await session.flush()
    employee = Employee(
        tenant_id=tenant.id,
        name="AI",
        role="customer_service",
        status="live",
        version="1.0.0",
    )
    session.add(employee)
    await session.flush()
    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=employee.id,
        employee_version="1.0.0",
        end_user_pseudo_id="u",
        channel="line",
        channel_user_id="U-1",
    )
    session.add(conv)
    await session.flush()

    msg_row = (
        await session.execute(
            text(
                "INSERT INTO message "
                "(id, conversation_id, seq, role, content, created_at) "
                "VALUES (gen_random_uuid(), :cid, 1, 'assistant', :c, NOW()) "
                "RETURNING id"
            ),
            {"cid": str(conv.id), "c": draft_text},
        )
    ).first()
    msg_id = uuid.UUID(str(msg_row[0]))  # type: ignore[index]

    out = OutboundMessage(
        tenant_id=tenant.id,
        conversation_id=conv.id,
        message_id=msg_id,
        channel="line",
        channel_user_id="U-1",
        status="awaiting_review",
    )
    session.add(out)
    await session.flush()
    return tenant, out, msg_id


async def test_api_list_reviews(client: AsyncClient, webhook_session: AsyncSession) -> None:
    await _seed_awaiting_review(webhook_session, slug_suffix="api-list")

    resp = await client.get("/api/v1/expert/reviews")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1
    item = body["items"][0]
    assert "outbound_id" in item
    assert "draft_text" in item


async def test_api_approve(client: AsyncClient, webhook_session: AsyncSession) -> None:
    _, out, _ = await _seed_awaiting_review(webhook_session, slug_suffix="api-appv")

    resp = await client.post(
        f"/api/v1/expert/reviews/{out.id}/approve",
        json={"expert_id": "expert-foo"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["new_status"] == "pending"


async def test_api_edit(client: AsyncClient, webhook_session: AsyncSession) -> None:
    _, out, _ = await _seed_awaiting_review(webhook_session, slug_suffix="api-edit")
    resp = await client.post(
        f"/api/v1/expert/reviews/{out.id}/edit",
        json={"expert_id": "x", "new_content": "改過的版本"},
    )
    assert resp.status_code == 200
    assert resp.json()["new_status"] == "pending"


async def test_api_reject(client: AsyncClient, webhook_session: AsyncSession) -> None:
    _, out, _ = await _seed_awaiting_review(webhook_session, slug_suffix="api-rej")
    resp = await client.post(
        f"/api/v1/expert/reviews/{out.id}/reject",
        json={
            "expert_id": "x",
            "reason": "AI 答案不正確",
            "handoff_message": "請接手",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["new_status"] == "rejected"
    assert data["handoff_id"] is not None


async def test_api_approve_409_when_wrong_status(
    client: AsyncClient,
    webhook_session: AsyncSession,
) -> None:
    _, out, _ = await _seed_awaiting_review(webhook_session, slug_suffix="api-409")
    out.status = "sent"
    await webhook_session.flush()

    resp = await client.post(
        f"/api/v1/expert/reviews/{out.id}/approve",
        json={"expert_id": "x"},
    )
    assert resp.status_code == 409


async def test_api_validation_error(
    client: AsyncClient,
    webhook_session: AsyncSession,
) -> None:
    """expert_id 空字串 → 422 Pydantic 驗證."""
    _, out, _ = await _seed_awaiting_review(webhook_session, slug_suffix="api-val")
    resp = await client.post(
        f"/api/v1/expert/reviews/{out.id}/approve",
        json={"expert_id": ""},
    )
    assert resp.status_code == 422
