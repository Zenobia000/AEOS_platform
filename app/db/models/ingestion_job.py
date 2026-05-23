"""IngestionJob — KB 上傳 → KnowledgeCard 的 pipeline 追蹤.

依 db-schema.md §4.3 + MC-008 (Knowledge RAG):
- 4 態 status: pending / processing / completed / failed
- 記錄產出幾張 KC + 錯誤訊息
- RLS by tenant_id
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base

INGESTION_STATUSES = ("pending", "processing", "completed", "failed")


class IngestionJob(Base):
    __tablename__ = "ingestion_job"

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
    source_file_ref: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="S3 path",
    )
    source_filename: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="original filename",
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    cards_created: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in INGESTION_STATUSES)})",
            name="status_check",
        ),
    )
