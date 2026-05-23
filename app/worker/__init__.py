"""Worker layer — 非同步處理器 + main loop.

Phase 1 包含：
- `DraftProcessor`: 對話一回合的 LLM draft 生成（webhook → LLM → outbound_message）
- `OutboundProcessor`: 把 pending outbound_message 推到 LINE Push API（含重試）
- `KbIngestProcessor`: 把 pending ingestion_job 跑成 KnowledgeCard drafts
- `run_loop` / `run_iteration`: polling 主迴圈（DraftPoll + OutboundPoll）
"""

from app.worker.draft_processor import DraftProcessor, DraftResult
from app.worker.kb_ingest import (
    IngestResult,
    KbIngestProcessor,
    chunk_text,
    find_pending_ingestion_jobs,
)
from app.worker.loop import (
    IterationResult,
    find_conversation_needing_draft,
    find_pending_outbound,
    run_iteration,
    run_loop,
)
from app.worker.outbound_processor import OutboundProcessor, PushResult

__all__ = [
    "DraftProcessor",
    "DraftResult",
    "IngestResult",
    "IterationResult",
    "KbIngestProcessor",
    "OutboundProcessor",
    "PushResult",
    "chunk_text",
    "find_conversation_needing_draft",
    "find_pending_ingestion_jobs",
    "find_pending_outbound",
    "run_iteration",
    "run_loop",
]
