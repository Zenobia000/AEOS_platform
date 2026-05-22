"""KnowledgeCard — RAG 的最小知識單元.

依 db-schema.md §4.2 + MC-008 (Knowledge RAG):
- 5 種 card_type: faq / policy / product / procedure / risk
- 3 態 status: draft / approved / archived
- pgvector(1024) embedding，ivfflat 餘弦相似度 index
- tags TEXT[] + GIN index 支援多標籤過濾
- RLS by tenant_id

UF-001 KB ingest 流程：上傳 → ingest pipeline 切片 → 產 KC draft → expert review → approve。
UF-003 / UF-004 對話時 RAG top-K=5 from approved KC（依 confidence threshold filter）。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base

KC_CARD_TYPES = ("faq", "policy", "product", "procedure", "risk")
KC_STATUSES = ("draft", "approved", "archived")

EMBEDDING_DIM = 1024  # voyage-3-lite / similar 1024-dim model


class KnowledgeCard(Base):
    __tablename__ = "knowledge_card"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant.id"),
        nullable=False,
    )
    card_type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default="{}",
    )
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_file_ref: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="S3 path to original uploaded file",
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    approved_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    valid_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIM),
        nullable=True,
        comment="pgvector embedding；voyage-3-lite or similar 1024-dim",
    )
    embedding_model: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="model 名稱用於 traceability",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            f"card_type IN ({', '.join(repr(t) for t in KC_CARD_TYPES)})",
            name="card_type_check",
        ),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in KC_STATUSES)})",
            name="status_check",
        ),
    )
