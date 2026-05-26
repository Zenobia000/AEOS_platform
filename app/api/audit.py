"""Audit Browse API — 把 append-only audit_log 視覺化 (S5).

對應 PRD-001 §5.5 + AC-005 expert 可追溯系統行為:
- GET /api/v1/audit/events            — 列 audit_log（filter tenant / event_type / since）
- GET /api/v1/audit/conversations     — 列 conversation 摘要（最新優先）
- GET /api/v1/audit/conversations/{id}— 單一 conversation 完整時間軸
  （messages + outbound + audit events 合併排序）
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select, text

from app.api.auth_dependency import current_expert
from app.db.models.audit_log import AuditLog
from app.db.models.conversation import Conversation
from app.db.models.outbound_message import OutboundMessage
from app.db.session import session_scope

router = APIRouter(
    prefix="/api/v1/audit",
    tags=["audit"],
    dependencies=[Depends(current_expert)],
)


@router.get("/events", summary="List audit events (含 resource_type / actor_id filter)")
async def list_events(
    tenant_id: Annotated[uuid.UUID | None, Query()] = None,
    event_type: Annotated[str | None, Query()] = None,
    resource_type: Annotated[str | None, Query()] = None,
    actor_id: Annotated[str | None, Query()] = None,
    since_hours: Annotated[int, Query(ge=1, le=720)] = 24,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> dict[str, object]:
    """Phase 1 後續 #4: 加 resource_type + actor_id filter（既有 tenant + event_type 維持）。"""
    since = datetime.now(UTC) - timedelta(hours=since_hours)
    async with session_scope() as session:
        stmt = (
            select(AuditLog)
            .where(AuditLog.occurred_at >= since)
            .order_by(desc(AuditLog.occurred_at))
            .limit(limit)
        )
        if tenant_id is not None:
            stmt = stmt.where(AuditLog.tenant_id == tenant_id)
        if event_type is not None:
            stmt = stmt.where(AuditLog.event_type == event_type)
        if resource_type is not None:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        rows = (await session.execute(stmt)).scalars().all()
        items = [
            {
                "id": str(r.id),
                "tenant_id": str(r.tenant_id) if r.tenant_id else None,
                "actor_id": r.actor_id,
                "event_type": r.event_type,
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "payload": r.payload,
                "occurred_at": r.occurred_at.isoformat(),
            }
            for r in rows
        ]
        return {"items": items, "count": len(items)}


@router.get("/conversations", summary="List conversations (most recent first)")
async def list_conversations(
    tenant_id: Annotated[uuid.UUID | None, Query()] = None,
    channel: Annotated[str | None, Query()] = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> dict[str, object]:
    async with session_scope() as session:
        stmt = (
            select(Conversation)
            .order_by(Conversation.last_message_at.desc().nulls_last())
            .limit(limit)
        )
        if tenant_id is not None:
            stmt = stmt.where(Conversation.tenant_id == tenant_id)
        if channel is not None:
            stmt = stmt.where(Conversation.channel == channel)
        if status_filter is not None:
            stmt = stmt.where(Conversation.status == status_filter)
        rows = (await session.execute(stmt)).scalars().all()
        items = [
            {
                "conversation_id": str(c.id),
                "tenant_id": str(c.tenant_id),
                "employee_id": str(c.employee_id),
                "channel": c.channel,
                "channel_user_id": c.channel_user_id,
                "status": c.status,
                "outcome": c.outcome,
                "message_count": c.message_count,
                "started_at": c.started_at.isoformat() if c.started_at else None,
                "last_message_at": (c.last_message_at.isoformat() if c.last_message_at else None),
                "ended_at": c.ended_at.isoformat() if c.ended_at else None,
            }
            for c in rows
        ]
        return {"items": items, "count": len(items)}


@router.get(
    "/conversations/{conversation_id}",
    summary="Full conversation timeline — messages + outbound + audit events",
)
async def conversation_detail(
    conversation_id: uuid.UUID,
) -> dict[str, object]:
    async with session_scope() as session:
        conv = (
            await session.execute(select(Conversation).where(Conversation.id == conversation_id))
        ).scalar_one_or_none()
        if conv is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"conversation {conversation_id} not found",
            )

        # messages（partitioned 表；用 raw SQL 較直覺）
        msg_rows = (
            await session.execute(
                text(
                    "SELECT id, seq, role, content, token_count, "
                    "       tool_invocations, created_at "
                    "FROM message WHERE conversation_id = :cid "
                    "ORDER BY seq ASC"
                ),
                {"cid": str(conv.id)},
            )
        ).all()
        messages = [
            {
                "id": str(r[0]),
                "seq": r[1],
                "role": r[2],
                "content": r[3],
                "token_count": r[4],
                "tool_invocations": r[5] or [],
                "created_at": r[6].isoformat() if r[6] else None,
            }
            for r in msg_rows
        ]

        # outbound 紀錄
        out_rows = (
            (
                await session.execute(
                    select(OutboundMessage)
                    .where(OutboundMessage.conversation_id == conversation_id)
                    .order_by(OutboundMessage.created_at.asc())
                )
            )
            .scalars()
            .all()
        )
        outbounds = [
            {
                "id": str(o.id),
                "message_id": str(o.message_id),
                "channel": o.channel,
                "status": o.status,
                "retry_count": o.retry_count,
                "error_message": o.error_message,
                "sent_at": o.sent_at.isoformat() if o.sent_at else None,
                "created_at": o.created_at.isoformat(),
            }
            for o in out_rows
        ]

        # audit events — 連同此 conversation + 與該 outbound 相關
        outbound_ids = [str(o.id) for o in out_rows]
        audit_stmt = (
            select(AuditLog)
            .where(
                (
                    (AuditLog.resource_type == "conversation")
                    & (AuditLog.resource_id == str(conv.id))
                )
                | (
                    (AuditLog.resource_type == "outbound_message")
                    & (AuditLog.resource_id.in_(outbound_ids or [""]))
                )
            )
            .order_by(AuditLog.occurred_at.asc())
        )
        audit_rows = (await session.execute(audit_stmt)).scalars().all()
        audits = [
            {
                "id": str(a.id),
                "event_type": a.event_type,
                "actor_id": a.actor_id,
                "resource_type": a.resource_type,
                "resource_id": a.resource_id,
                "payload": a.payload,
                "occurred_at": a.occurred_at.isoformat(),
            }
            for a in audit_rows
        ]

        return {
            "conversation": {
                "id": str(conv.id),
                "tenant_id": str(conv.tenant_id),
                "employee_id": str(conv.employee_id),
                "channel": conv.channel,
                "channel_user_id": conv.channel_user_id,
                "status": conv.status,
                "outcome": conv.outcome,
                "message_count": conv.message_count,
                "started_at": conv.started_at.isoformat() if conv.started_at else None,
                "last_message_at": (
                    conv.last_message_at.isoformat() if conv.last_message_at else None
                ),
                "ended_at": conv.ended_at.isoformat() if conv.ended_at else None,
            },
            "messages": messages,
            "outbounds": outbounds,
            "audit_events": audits,
        }


# Phase 1 後續 #5: Conversation GDPR export ─────────


@router.get(
    "/conversations/{conversation_id}/export",
    summary="Export 完整 conversation 為 JSON（GDPR-ready）",
)
async def export_conversation(conversation_id: uuid.UUID) -> dict[str, object]:
    """完整 dump 一個 conversation 的所有資料：
    conversation row + 所有 message + 所有 outbound + 所有 audit event。
    """
    async with session_scope() as session:
        conv_row = (
            await session.execute(
                text(
                    "SELECT id, tenant_id, employee_id, channel, status, outcome, "
                    "started_at, ended_at, message_count, summary "
                    "FROM conversation WHERE id = :cid"
                ),
                {"cid": str(conversation_id)},
            )
        ).first()
        if conv_row is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="conversation not found")

        msg_rows = (
            await session.execute(
                text(
                    "SELECT id, seq, role, content, token_count, "
                    "tool_invocations, skill_version_id, created_at "
                    "FROM message WHERE conversation_id = :cid ORDER BY seq"
                ),
                {"cid": str(conversation_id)},
            )
        ).all()
        out_rows = (
            await session.execute(
                text(
                    "SELECT id, status, retry_count, error_message, "
                    "sent_at, created_at FROM outbound_message "
                    "WHERE conversation_id = :cid ORDER BY created_at"
                ),
                {"cid": str(conversation_id)},
            )
        ).all()
        # 收 audit events: resource_id 為此 conversation OR 此 conv 的任一 outbound/message
        related_ids = [str(conversation_id)]
        related_ids.extend(str(r[0]) for r in msg_rows)
        related_ids.extend(str(r[0]) for r in out_rows)
        audit_rows = (
            (
                await session.execute(
                    select(AuditLog)
                    .where(AuditLog.resource_id.in_(related_ids))
                    .order_by(AuditLog.occurred_at)
                )
            )
            .scalars()
            .all()
        )

        return {
            "schema_version": "1.0",
            "exported_at": datetime.now(UTC).isoformat(),
            "conversation": {
                "id": str(conv_row[0]),
                "tenant_id": str(conv_row[1]),
                "employee_id": str(conv_row[2]),
                "channel": conv_row[3],
                "status": conv_row[4],
                "outcome": conv_row[5],
                "started_at": conv_row[6].isoformat() if conv_row[6] else None,
                "ended_at": conv_row[7].isoformat() if conv_row[7] else None,
                "message_count": conv_row[8],
                "summary": conv_row[9],
            },
            "messages": [
                {
                    "id": str(r[0]),
                    "seq": r[1],
                    "role": r[2],
                    "content": r[3],
                    "token_count": r[4],
                    "tool_invocations": r[5],
                    "skill_version_id": str(r[6]) if r[6] else None,
                    "created_at": r[7].isoformat(),
                }
                for r in msg_rows
            ],
            "outbound_messages": [
                {
                    "id": str(r[0]),
                    "status": r[1],
                    "retry_count": r[2],
                    "error_message": r[3],
                    "sent_at": r[4].isoformat() if r[4] else None,
                    "created_at": r[5].isoformat(),
                }
                for r in out_rows
            ],
            "audit_events": [
                {
                    "id": str(a.id),
                    "event_type": a.event_type,
                    "actor_id": a.actor_id,
                    "payload": a.payload,
                    "occurred_at": a.occurred_at.isoformat(),
                }
                for a in audit_rows
            ],
        }
