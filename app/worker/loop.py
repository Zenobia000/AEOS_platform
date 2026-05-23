"""Worker main loop — 串接 Tier 0~4 + S3 TestSet 的 polling cycles.

依 MC-009 + MC-010 + MC-011 + PRD-001 §5.2 + §5.4-5.5：
- IdlePoll: 先把 30min 沒互動的 conversation 收 closed
- DraftPoll: 找「最後一則 message 是 user」的 active conversation → DraftProcessor
- OutboundPoll: 找 status IN ('pending','retrying') 的 outbound_message → OutboundProcessor
- TestRunPoll: 找 status='pending' 的 test_run → TestSetRunner（可選；無 LLM 時略過）

Phase 1 簡化：
- 用 SELECT ... FOR UPDATE SKIP LOCKED 避免並發處理同一筆
- 單 process 內 sequential；Phase 2 多 worker + Redis queue
- TestRunPoll 預設 max 1/iter（test run 跑時間長，避免阻塞 draft cycle）
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models.outbound_message import OutboundMessage
from app.db.models.test_run import TestRun
from app.services.conversation_idle import close_idle_conversations
from app.worker.draft_processor import DraftProcessor, DraftResult
from app.worker.outbound_processor import OutboundProcessor, PushResult
from app.worker.test_runner import TestSetRunner

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
    test_runs_processed: int = 0
    test_runs_failed: int = 0

    @property
    def did_work(self) -> bool:
        return (
            self.drafts_processed
            + self.drafts_failed
            + self.outbounds_processed
            + self.outbounds_failed
            + self.idle_closed
            + self.test_runs_processed
            + self.test_runs_failed
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
    """找 pending / retrying 的 outbound_message，依 created_at asc."""
    stmt = (
        select(OutboundMessage)
        .where(OutboundMessage.status.in_(["pending", "retrying"]))
        .order_by(OutboundMessage.created_at.asc())
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    return list((await session.execute(stmt)).scalars().all())


async def find_pending_test_runs(
    session: AsyncSession,
    *,
    limit: int = 1,
) -> list[TestRun]:
    """找 status='pending' 的 test_run，依 created_at asc.

    SELECT FOR UPDATE SKIP LOCKED 避免並發處理（test run 跑 LLM 開銷
    高，並發抓重複會浪費 token）。
    """
    stmt = (
        select(TestRun)
        .where(TestRun.status == "pending")
        .order_by(TestRun.created_at.asc())
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    return list((await session.execute(stmt)).scalars().all())


async def run_iteration(
    session: AsyncSession,
    *,
    draft_processor: DraftProcessor,
    outbound_processor: OutboundProcessor,
    test_set_runner: TestSetRunner | None = None,
    skill_slug: str = DEFAULT_SKILL_SLUG,
    skill_version: str = DEFAULT_SKILL_VERSION,
    max_drafts_per_iter: int = 5,
    max_outbounds_per_iter: int = 5,
    max_test_runs_per_iter: int = 1,
) -> IterationResult:
    """跑一次完整 iteration：idle close + draft + outbound + test_run cycles.

    Args:
        session: async DB session（caller 管理 transaction; 本函式 flush 但不 commit）
        draft_processor / outbound_processor: 必要 processors
        test_set_runner: 可選；None 則跳過 test_run cycle（無 LLM 環境 / 純 demo）
        skill_slug / skill_version: Phase 1 唯一 skill
        max_*_per_iter: 每 iter 上限避免長 transaction
    """
    drafts_processed = 0
    drafts_failed = 0
    outbounds_processed = 0
    outbounds_failed = 0
    test_runs_processed = 0
    test_runs_failed = 0

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

    # ── Test run cycle（可選） ───────────────────
    if test_set_runner is not None:
        for _ in range(max_test_runs_per_iter):
            runs = await find_pending_test_runs(session, limit=1)
            if not runs:
                break
            run = runs[0]
            try:
                await test_set_runner.run(session, run_id=run.id)
                test_runs_processed += 1
            except Exception:
                test_runs_failed += 1

    return IterationResult(
        drafts_processed=drafts_processed,
        drafts_failed=drafts_failed,
        outbounds_processed=outbounds_processed,
        outbounds_failed=outbounds_failed,
        idle_closed=idle_result.closed_count,
        test_runs_processed=test_runs_processed,
        test_runs_failed=test_runs_failed,
    )


async def run_loop(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    draft_processor: DraftProcessor,
    outbound_processor: OutboundProcessor,
    test_set_runner: TestSetRunner | None = None,
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
                    test_set_runner=test_set_runner,
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
    "find_pending_test_runs",
    "run_iteration",
    "run_loop",
]
