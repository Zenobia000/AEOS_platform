"""Worker main loop — 兩個 polling cycles 串接 Tier 0~4 的執行流程.

依 MC-009 + MC-010 + MC-011 + PRD-001 §5.4-5.5：
- DraftPoll: 找「最後一則 message 是 user」的 active conversation → DraftProcessor
- OutboundPoll: 找 status IN ('pending','retrying') 的 outbound_message → OutboundProcessor

Phase 1 簡化：
- 用 SELECT ... FOR UPDATE SKIP LOCKED 避免並發處理同一筆
- 單 process 內 sequential（先 draft、再 outbound）；Phase 2 多 worker + Redis queue
- 沒做 backoff scheduling — retrying 的 outbound 立即下次 cycle 再嘗試（無 delay）
- DraftProcessor 失敗目前不寫 conversation 狀態（仍待重試）— Phase 2 加 dead_letter
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models.outbound_message import OutboundMessage
from app.services.conversation_idle import close_idle_conversations
from app.worker.draft_processor import DraftProcessor, DraftResult
from app.worker.outbound_processor import OutboundProcessor, PushResult

# 預設 skill — Phase 1 唯一 skill
DEFAULT_SKILL_SLUG = "customer-service/faq-respond"
DEFAULT_SKILL_VERSION = "v1.0.0"


@dataclass(frozen=True)
class IterationResult:
    """`run_iteration()` 回傳值."""

    drafts_processed: int
    drafts_failed: int
    outbounds_processed: int
    outbounds_failed: int
    idle_closed: int = 0

    @property
    def did_work(self) -> bool:
        return (
            self.drafts_processed
            + self.drafts_failed
            + self.outbounds_processed
            + self.outbounds_failed
            + self.idle_closed
        ) > 0


async def find_conversation_needing_draft(
    session: AsyncSession,
    *,
    limit: int = 1,
) -> list[uuid.UUID]:
    """找 active conversation 且最後一則 message 是 user。

    用 LATERAL JOIN 取每個 conversation 最後一則 message 的 role；
    SELECT FOR UPDATE SKIP LOCKED 避免並發處理同一筆。
    """
    rows = (
        await session.execute(
            text(
                "SELECT c.id "
                "FROM conversation c "
                "JOIN LATERAL ("
                "  SELECT role FROM message "
                "  WHERE conversation_id = c.id "
                "  ORDER BY seq DESC LIMIT 1"
                ") last_msg ON true "
                "WHERE c.status IN ('open', 'active') "
                "  AND last_msg.role = 'user' "
                "ORDER BY c.last_message_at ASC NULLS LAST "
                "LIMIT :lim "
                "FOR UPDATE OF c SKIP LOCKED"
            ),
            {"lim": limit},
        )
    ).all()
    return [uuid.UUID(str(r[0])) for r in rows]


async def find_pending_outbound(
    session: AsyncSession,
    *,
    limit: int = 1,
) -> list[OutboundMessage]:
    """找 pending / retrying 的 outbound_message，依 created_at asc.

    SELECT FOR UPDATE SKIP LOCKED 避免並發處理。
    """
    from sqlalchemy import select

    stmt = (
        select(OutboundMessage)
        .where(OutboundMessage.status.in_(["pending", "retrying"]))
        .order_by(OutboundMessage.created_at.asc())
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    return list((await session.execute(stmt)).scalars().all())


async def run_iteration(
    session: AsyncSession,
    *,
    draft_processor: DraftProcessor,
    outbound_processor: OutboundProcessor,
    skill_slug: str = DEFAULT_SKILL_SLUG,
    skill_version: str = DEFAULT_SKILL_VERSION,
    max_drafts_per_iter: int = 5,
    max_outbounds_per_iter: int = 5,
) -> IterationResult:
    """跑一次完整 iteration：draft cycle + outbound cycle.

    Args:
        session: async DB session（caller 管理 transaction; 本函式 flush 但不 commit）
        draft_processor / outbound_processor: 已初始化好的 processors
        skill_slug / skill_version: Phase 1 唯一 skill
        max_drafts_per_iter / max_outbounds_per_iter: 每 iter 上限避免長 transaction
    """
    drafts_processed = 0
    drafts_failed = 0
    outbounds_processed = 0
    outbounds_failed = 0

    # ── Idle close cycle（先跑，免得 draft cycle 處理已 stale 的對話）
    idle_result = await close_idle_conversations(session)

    # ── Draft cycle ──────────────────────────────
    for _ in range(max_drafts_per_iter):
        conv_ids = await find_conversation_needing_draft(session, limit=1)
        if not conv_ids:
            break
        conv_id = conv_ids[0]
        try:
            await draft_processor.process_message(
                session=session,
                conversation_id=conv_id,
                skill_slug=skill_slug,
                skill_version=skill_version,
            )
            drafts_processed += 1
        except Exception:
            drafts_failed += 1

    # ── Outbound cycle ───────────────────────────
    for _ in range(max_outbounds_per_iter):
        outbounds = await find_pending_outbound(session, limit=1)
        if not outbounds:
            break
        outbound = outbounds[0]
        try:
            await outbound_processor.process_one(session, outbound)
            outbounds_processed += 1
        except Exception:
            outbounds_failed += 1

    return IterationResult(
        drafts_processed=drafts_processed,
        drafts_failed=drafts_failed,
        outbounds_processed=outbounds_processed,
        outbounds_failed=outbounds_failed,
        idle_closed=idle_result.closed_count,
    )


async def run_loop(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    draft_processor: DraftProcessor,
    outbound_processor: OutboundProcessor,
    interval_s: float = 1.0,
    stop_event: asyncio.Event | None = None,
    skill_slug: str = DEFAULT_SKILL_SLUG,
    skill_version: str = DEFAULT_SKILL_VERSION,
) -> None:
    """長跑 loop：每 interval_s 秒跑一次 run_iteration，直到 stop_event 觸發.

    每個 iteration 一個新 session（transaction 完整提交，避免長 lock）.
    """
    stop = stop_event or asyncio.Event()
    while not stop.is_set():
        async with session_factory() as session:
            await session.begin()
            try:
                await run_iteration(
                    session,
                    draft_processor=draft_processor,
                    outbound_processor=outbound_processor,
                    skill_slug=skill_slug,
                    skill_version=skill_version,
                )
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        try:
            await asyncio.wait_for(stop.wait(), timeout=interval_s)
        except TimeoutError:
            continue


__all__ = [
    "DEFAULT_SKILL_SLUG",
    "DEFAULT_SKILL_VERSION",
    "DraftResult",
    "IterationResult",
    "PushResult",
    "find_conversation_needing_draft",
    "find_pending_outbound",
    "run_iteration",
    "run_loop",
]
