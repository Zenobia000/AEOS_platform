"""Conversation idle timeout — S4 收尾.

對應 MC-010 + PRD-001 §5.4 / SAD §session lifecycle:
- 30 分鐘無互動的 open / active conversation → status='closed', outcome='abandoned'
- 跑 audit conversation.idle_closed（每筆）
- 利用既有 partial index idx_conv_idle（status IN open/active/waiting_human, last_message_at）

Phase 1：
- 同 worker loop 一起跑（每 iteration 順帶清一次）；不額外開 cron
- waiting_human 暫不自動關（expert 接手中；S5 再評估）
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.conversation import Conversation
from app.services import audit

DEFAULT_IDLE_TIMEOUT = timedelta(minutes=30)
DEFAULT_BATCH_LIMIT = 50


@dataclass(frozen=True)
class IdleCloseResult:
    closed_count: int
    closed_ids: Sequence[str]


async def close_idle_conversations(
    session: AsyncSession,
    *,
    idle_timeout: timedelta = DEFAULT_IDLE_TIMEOUT,
    limit: int = DEFAULT_BATCH_LIMIT,
    now: datetime | None = None,
) -> IdleCloseResult:
    """掃 idle conversation 並收尾.

    Args:
        idle_timeout: 多久沒互動視為 idle（預設 30 min）
        limit: 一次 batch 最大筆數（避免長 transaction）
        now: 注入用（測試）；None = datetime.now(UTC)

    Returns:
        IdleCloseResult — 含關閉的 conversation_id 清單
    """
    cutoff = (now or datetime.now(UTC)) - idle_timeout

    # 撈待關的 conversation（ORM）；FOR UPDATE SKIP LOCKED 避免並發
    stmt = (
        select(Conversation)
        .where(
            Conversation.status.in_(("open", "active")),
            Conversation.last_message_at.is_not(None),
            Conversation.last_message_at < cutoff,
        )
        .order_by(Conversation.last_message_at.asc())
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    rows = list((await session.execute(stmt)).scalars().all())
    if not rows:
        return IdleCloseResult(closed_count=0, closed_ids=[])

    now_ts = now or datetime.now(UTC)
    closed_ids: list[str] = []
    for conv in rows:
        conv.status = "closed"
        conv.outcome = "abandoned"
        conv.ended_at = now_ts
        await session.flush()
        await audit.emit(
            session,
            event_type="conversation.idle_closed",
            tenant_id=conv.tenant_id,
            actor_id="idle_timeout_worker",
            resource_type="conversation",
            resource_id=str(conv.id),
            payload={"idle_timeout_seconds": int(idle_timeout.total_seconds())},
        )
        closed_ids.append(str(conv.id))

    return IdleCloseResult(closed_count=len(closed_ids), closed_ids=closed_ids)
