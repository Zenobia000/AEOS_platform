"""ExpertReview service 單元測試 — approve / edit / reject / list_pending."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog
from app.db.models.conversation import Conversation
from app.db.models.conversation_handoff import ConversationHandoff
from app.db.models.employee import Employee
from app.db.models.outbound_message import OutboundMessage
from app.db.models.tenant import Tenant
from app.services import expert_review


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


async def test_approve_transitions_to_pending(db_session: AsyncSession) -> None:
    _, out, _ = await _seed_awaiting_review(db_session, slug_suffix="appv")
    result = await expert_review.approve(db_session, outbound_id=out.id, expert_id="expert-jenny")

    assert result.action == "approved"
    assert result.new_status == "pending"

    refreshed = (
        await db_session.execute(select(OutboundMessage).where(OutboundMessage.id == out.id))
    ).scalar_one()
    assert refreshed.status == "pending"

    audit_row = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.event_type == "expert.draft_approved")
        )
    ).scalar_one()
    assert audit_row.actor_id == "expert-jenny"


async def test_edit_updates_message_and_approves(db_session: AsyncSession) -> None:
    _, out, msg_id = await _seed_awaiting_review(db_session, slug_suffix="edit")
    new_text = "您好，本店退貨可於到貨後 14 天內申請（小編改過的版本）"

    result = await expert_review.edit_and_approve(
        db_session,
        outbound_id=out.id,
        new_content=new_text,
        expert_id="expert-amy",
    )
    assert result.action == "edited"
    assert result.new_status == "pending"

    content = (
        await db_session.execute(
            text("SELECT content FROM message WHERE id = :mid"),
            {"mid": str(msg_id)},
        )
    ).scalar_one()
    assert content == new_text

    refreshed = (
        await db_session.execute(select(OutboundMessage).where(OutboundMessage.id == out.id))
    ).scalar_one()
    assert refreshed.status == "pending"

    audit_row = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.event_type == "expert.draft_edited")
        )
    ).scalar_one()
    assert audit_row.payload["new_length"] == len(new_text)


async def test_reject_creates_handoff(db_session: AsyncSession) -> None:
    _, out, _ = await _seed_awaiting_review(db_session, slug_suffix="rej")
    result = await expert_review.reject(
        db_session,
        outbound_id=out.id,
        reason="AI 答錯：實際是 14 天而非 7 天",
        expert_id="expert-ben",
        handoff_message="請接手處理這個 case",
    )
    assert result.action == "rejected"
    assert result.handoff_id is not None

    refreshed = (
        await db_session.execute(select(OutboundMessage).where(OutboundMessage.id == out.id))
    ).scalar_one()
    assert refreshed.status == "rejected"

    handoff = (
        await db_session.execute(
            select(ConversationHandoff).where(ConversationHandoff.id == result.handoff_id)
        )
    ).scalar_one()
    assert handoff.from_conversation_id == out.conversation_id
    assert handoff.expert_id == "expert-ben"
    assert "請接手" in (handoff.handoff_message or "")

    audit_row = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.event_type == "expert.draft_rejected")
        )
    ).scalar_one()
    assert "14 天" in audit_row.payload["reason"]


async def test_approve_rejects_wrong_status(db_session: AsyncSession) -> None:
    _, out, _ = await _seed_awaiting_review(db_session, slug_suffix="wrong-st")
    out.status = "sent"
    await db_session.flush()

    with pytest.raises(expert_review.ExpertReviewError, match="awaiting_review"):
        await expert_review.approve(db_session, outbound_id=out.id, expert_id="x")


async def test_approve_unknown_outbound_raises(db_session: AsyncSession) -> None:
    with pytest.raises(expert_review.ExpertReviewError, match="not found"):
        await expert_review.approve(db_session, outbound_id=uuid.uuid4(), expert_id="x")


async def test_edit_empty_content_raises(db_session: AsyncSession) -> None:
    _, out, _ = await _seed_awaiting_review(db_session, slug_suffix="empty-edit")
    with pytest.raises(expert_review.ExpertReviewError, match="empty"):
        await expert_review.edit_and_approve(
            db_session,
            outbound_id=out.id,
            new_content="   ",
            expert_id="x",
        )


async def test_list_pending_returns_drafts(db_session: AsyncSession) -> None:
    tenant, out, _ = await _seed_awaiting_review(db_session, slug_suffix="list")
    items = await expert_review.list_pending(db_session, tenant_id=tenant.id)
    assert len(items) == 1
    item = items[0]
    assert item["outbound_id"] == str(out.id)
    draft_text = item["draft_text"]
    assert isinstance(draft_text, str)
    assert "退貨" in draft_text
    assert item["channel"] == "line"


async def test_list_pending_filters_other_status(db_session: AsyncSession) -> None:
    tenant, out, _ = await _seed_awaiting_review(db_session, slug_suffix="list-filter")
    out.status = "pending"
    await db_session.flush()

    items = await expert_review.list_pending(db_session, tenant_id=tenant.id)
    assert items == []
