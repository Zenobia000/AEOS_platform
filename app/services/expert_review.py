"""ExpertReview service — Draft Mode approve / edit / reject.

依 PRD-001 §5.4 F-DFT-01/02/03:
- F-DFT-01: AI 產 draft → outbound_message.status='awaiting_review'
- F-DFT-02: Expert 可 (a) 1-click approve / (b) edit-and-send / (c) reject
- F-DFT-03: 所有 approve/edit/reject 進 audit log（作為下次 Skill 訓練素材）

行為：
- approve(outbound_id, expert_id): status='awaiting_review' → 'pending'
  → OutboundProcessor 將撿並 Push
- edit_and_approve(outbound_id, new_content, expert_id):
  UPDATE message.content + 'pending'
- reject(outbound_id, reason, expert_id, handoff_message=None):
  status='rejected' + 建 conversation_handoff (status=pending; expert 接手)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.conversation_handoff import ConversationHandoff
from app.db.models.outbound_message import OutboundMessage
from app.services import audit


class ExpertReviewError(RuntimeError):
    """Expert action 無法執行（status 不對 / outbound 不存在等）。"""


@dataclass(frozen=True)
class ReviewActionResult:
    """approve / edit / reject 通用回傳."""

    outbound_id: uuid.UUID
    action: Literal["approved", "edited", "rejected"]
    new_status: str
    handoff_id: uuid.UUID | None = None


async def _load_awaiting(session: AsyncSession, outbound_id: uuid.UUID) -> OutboundMessage:
    out = (
        await session.execute(select(OutboundMessage).where(OutboundMessage.id == outbound_id))
    ).scalar_one_or_none()
    if out is None:
        raise ExpertReviewError(f"outbound_message {outbound_id} not found")
    if out.status != "awaiting_review":
        raise ExpertReviewError(
            f"outbound {outbound_id} not in awaiting_review (status={out.status})"
        )
    return out


async def approve(
    session: AsyncSession,
    *,
    outbound_id: uuid.UUID,
    expert_id: str,
) -> ReviewActionResult:
    """Expert 1-click approve → status='pending'."""
    out = await _load_awaiting(session, outbound_id)
    out.status = "pending"
    out.error_message = None
    await session.flush()

    await audit.emit(
        session,
        event_type="expert.draft_approved",
        tenant_id=out.tenant_id,
        actor_id=expert_id,
        resource_type="outbound_message",
        resource_id=str(out.id),
        payload={
            "channel": out.channel,
            "conversation_id": str(out.conversation_id),
            "message_id": str(out.message_id),
        },
    )
    return ReviewActionResult(
        outbound_id=out.id,
        action="approved",
        new_status="pending",
    )


async def edit_and_approve(
    session: AsyncSession,
    *,
    outbound_id: uuid.UUID,
    new_content: str,
    expert_id: str,
) -> ReviewActionResult:
    """Expert 編輯 draft → UPDATE message.content → status='pending'."""
    out = await _load_awaiting(session, outbound_id)
    if not new_content.strip():
        raise ExpertReviewError("new_content cannot be empty")

    # UPDATE message (用 id 即可；複合 PK 但 id 來自 gen_random_uuid)
    result = await session.execute(
        text("UPDATE message SET content = :c WHERE id = :mid"),
        {"c": new_content, "mid": str(out.message_id)},
    )
    rowcount: int = getattr(result, "rowcount", 0) or 0
    if rowcount == 0:
        raise ExpertReviewError(f"underlying message {out.message_id} not found")

    out.status = "pending"
    out.error_message = None
    await session.flush()

    await audit.emit(
        session,
        event_type="expert.draft_edited",
        tenant_id=out.tenant_id,
        actor_id=expert_id,
        resource_type="outbound_message",
        resource_id=str(out.id),
        payload={
            "channel": out.channel,
            "conversation_id": str(out.conversation_id),
            "message_id": str(out.message_id),
            "new_length": len(new_content),
        },
    )
    return ReviewActionResult(
        outbound_id=out.id,
        action="edited",
        new_status="pending",
    )


async def reject(
    session: AsyncSession,
    *,
    outbound_id: uuid.UUID,
    reason: str,
    expert_id: str,
    handoff_message: str | None = None,
) -> ReviewActionResult:
    """Expert 拒絕 draft → status='rejected' + 建 conversation_handoff (pending)."""
    out = await _load_awaiting(session, outbound_id)

    out.status = "rejected"
    out.error_message = f"rejected by {expert_id}: {reason[:200]}"
    await session.flush()

    handoff = ConversationHandoff(
        from_conversation_id=out.conversation_id,
        reason="user_request",  # expert 主動拒絕 = user_request 屬性最近
        handoff_message=handoff_message or f"draft rejected: {reason[:200]}",
        expert_id=expert_id,
    )
    session.add(handoff)
    await session.flush()

    await audit.emit(
        session,
        event_type="expert.draft_rejected",
        tenant_id=out.tenant_id,
        actor_id=expert_id,
        resource_type="outbound_message",
        resource_id=str(out.id),
        payload={
            "channel": out.channel,
            "conversation_id": str(out.conversation_id),
            "handoff_id": str(handoff.id),
            "reason": reason[:500],
        },
    )
    return ReviewActionResult(
        outbound_id=out.id,
        action="rejected",
        new_status="rejected",
        handoff_id=handoff.id,
    )


async def list_pending(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID | None = None,
    limit: int = 50,
) -> list[dict[str, object]]:
    """列出 awaiting_review 的 outbound_message + 對應 draft text。

    Returns list of dicts: {outbound_id, conversation_id, channel,
    channel_user_id, message_id, draft_text, created_at}.
    """
    sql = (
        "SELECT o.id, o.conversation_id, o.channel, o.channel_user_id, "
        "       o.message_id, m.content, o.created_at "
        "FROM outbound_message o "
        "LEFT JOIN message m ON m.id = o.message_id "
        "WHERE o.status = 'awaiting_review' "
    )
    params: dict[str, object] = {"lim": limit}
    if tenant_id is not None:
        sql += "AND o.tenant_id = :tid "
        params["tid"] = str(tenant_id)
    sql += "ORDER BY o.created_at ASC LIMIT :lim"

    rows = (await session.execute(text(sql), params)).all()
    return [
        {
            "outbound_id": str(row[0]),
            "conversation_id": str(row[1]),
            "channel": row[2],
            "channel_user_id": row[3],
            "message_id": str(row[4]),
            "draft_text": row[5],
            "created_at": row[6].isoformat() if row[6] is not None else None,
        }
        for row in rows
    ]
