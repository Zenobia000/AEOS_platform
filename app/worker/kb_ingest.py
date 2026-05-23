"""KbIngestProcessor — 把 ingestion_job 跑成 KnowledgeCard drafts.

依 PRD-001 §5.1 F-KB-01~05 + MC-008 + db-schema.md §4.2-4.3:
- 撿 status='pending' 的 ingestion_job
- 用 file_loader(source_file_ref) 取得 bytes（Phase 1：caller 提供；S3 接線 S5）
- parse_bytes(filename) → text
- chunk_text() 切片（固定 chunk size + overlap）
- embed via EmbeddingClient (1024 dim)
- 每 chunk INSERT knowledge_card (status='draft', card_type='faq' 預設)
- UPDATE ingestion_job (completed/failed + cards_created + completed_at)

Phase 1 簡化：
- card_type 預設 'faq'；未做自動分類（S3 LLM judge 接上後改）
- title 取 chunk 前 60 字；S3 LLM 產 title + summary（F-KB-03）
- 不做缺漏資料反向提示（F-KB-05 需 KC 與客服 log 對照，待真資料）
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ingestion_job import IngestionJob
from app.db.models.knowledge_card import KnowledgeCard
from app.embeddings import EmbeddingClient

# Chunking 預設（PRD-001 §5.1 F-KB-03）
DEFAULT_CHUNK_SIZE = 800  # 字元
DEFAULT_CHUNK_OVERLAP = 80  # 字元
DEFAULT_CARD_TYPE = "faq"
DEFAULT_STATUS = "draft"

FileLoader = Callable[[str], Awaitable[bytes]]


@dataclass(frozen=True)
class IngestResult:
    """`process_one()` 回傳值."""

    ingestion_job_id: uuid.UUID
    status: str  # completed / failed
    cards_created: int
    error: str | None = None


def chunk_text(
    text_content: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """固定大小 chunk + overlap，跳過空白 chunk."""
    if not text_content.strip():
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be in [0, chunk_size)")

    chunks: list[str] = []
    stride = chunk_size - overlap
    pos = 0
    while pos < len(text_content):
        piece = text_content[pos : pos + chunk_size].strip()
        if piece:
            chunks.append(piece)
        pos += stride
    return chunks


class KbIngestProcessor:
    """跑單一 ingestion_job 的處理器.

    Args:
        embedder: EmbeddingClient（Phase 1 預設 StubEmbeddingClient；prod 用 Voyage）
        file_loader: 異步 callable(source_file_ref) -> bytes
                     Phase 1 caller 提供（local file / S3 都包成這個介面）
        chunk_size / overlap: chunking 參數
    """

    def __init__(
        self,
        *,
        embedder: EmbeddingClient,
        file_loader: FileLoader,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        self._embedder = embedder
        self._file_loader = file_loader
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    async def process_one(
        self,
        session: AsyncSession,
        job: IngestionJob,
    ) -> IngestResult:
        """跑單一 job：load → parse → chunk → embed → upsert KC + update job."""
        # 標 processing
        job.status = "processing"
        await session.flush()

        try:
            data = await self._file_loader(job.source_file_ref)
            from app.parsers import parse_bytes

            full_text = parse_bytes(data, job.source_filename)
            chunks = chunk_text(
                full_text,
                chunk_size=self._chunk_size,
                overlap=self._chunk_overlap,
            )
            if not chunks:
                return await self._complete(session, job, cards_created=0)

            embedding_result = await self._embedder.embed(chunks)
            cards_inserted = await self._insert_cards(
                session,
                job=job,
                chunks=chunks,
                vectors=[list(v) for v in embedding_result.vectors],
                embedding_model=embedding_result.model,
            )
            return await self._complete(session, job, cards_created=cards_inserted)
        except Exception as exc:
            return await self._fail(session, job, error=str(exc))

    # ── status transitions ──────────────────────────

    async def _complete(
        self,
        session: AsyncSession,
        job: IngestionJob,
        *,
        cards_created: int,
    ) -> IngestResult:
        job.status = "completed"
        job.cards_created = cards_created
        await session.execute(
            text("UPDATE ingestion_job SET completed_at = NOW() WHERE id = :jid"),
            {"jid": str(job.id)},
        )
        await session.flush()
        return IngestResult(
            ingestion_job_id=job.id,
            status="completed",
            cards_created=cards_created,
        )

    async def _fail(
        self,
        session: AsyncSession,
        job: IngestionJob,
        *,
        error: str,
    ) -> IngestResult:
        job.status = "failed"
        job.error_message = error[:1000]
        await session.flush()
        return IngestResult(
            ingestion_job_id=job.id,
            status="failed",
            cards_created=0,
            error=error,
        )

    # ── KC writes ────────────────────────────────────

    async def _insert_cards(
        self,
        session: AsyncSession,
        *,
        job: IngestionJob,
        chunks: list[str],
        vectors: list[list[float]],
        embedding_model: str,
    ) -> int:
        """每個 chunk 寫一張 KnowledgeCard (status='draft')."""
        assert len(chunks) == len(vectors), "chunks vs vectors mismatch"

        for chunk, vec in zip(chunks, vectors, strict=True):
            title = _make_title(chunk)
            kc = KnowledgeCard(
                tenant_id=job.tenant_id,
                card_type=DEFAULT_CARD_TYPE,
                title=title,
                body_markdown=chunk,
                status=DEFAULT_STATUS,
                source_file_ref=job.source_file_ref,
                embedding=vec,
                embedding_model=embedding_model,
            )
            session.add(kc)
        await session.flush()
        return len(chunks)


def _make_title(chunk: str, *, max_chars: int = 60) -> str:
    """Phase 1: 取 chunk 第一個非空行的前 max_chars 字當 title."""
    for line in chunk.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:max_chars]
    return chunk.strip()[:max_chars] or "(empty)"


async def find_pending_ingestion_jobs(
    session: AsyncSession,
    *,
    limit: int = 1,
) -> list[IngestionJob]:
    """撿 status='pending' 的 ingestion_job，依 created_at asc, FOR UPDATE SKIP LOCKED."""
    stmt = (
        select(IngestionJob)
        .where(IngestionJob.status == "pending")
        .order_by(IngestionJob.created_at.asc())
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    return list((await session.execute(stmt)).scalars().all())
