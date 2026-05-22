"""Conversation aggregate root.

依 db-schema.md §4.4 + MC-010 (Conversation Engine):
- 6 態 status: open / active / waiting_human / resolved / closed / archived
- channel 限 line / web_chat / whatsapp
- outcome 4 種（含 NULL）
- summary 為 L2.5 session summary（對話結束時由 Haiku 生成，ADR-0010）
- end_user_pseudo_id / channel_user_id 都是 pseudonymized（ADR-0005）
- employee_version 是 conversation 開始時的 snapshot：Frozen Runtime
  原則確保整段對話不被後續 employee 更新影響
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base

CONV_CHANNELS = ("line", "web_chat", "whatsapp")
CONV_STATUSES = (
    "open",
    "active",
    "waiting_human",
    "resolved",
    "closed",
    "archived",
)
CONV_OUTCOMES = ("resolved", "handoff_human", "abandoned", "error")


class Conversation(Base):
    __tablename__ = "conversation"

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
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employee.id"),
        nullable=False,
    )
    employee_version: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="snapshot version at conversation start",
    )
    end_user_pseudo_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="pseudonymized (ADR-0005)",
    )
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    channel_user_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="channel-specific user ID (hashed)",
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="open",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="for idle timeout detection",
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="L2.5 session summary (generated on close)",
    )
    message_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="denormalized counter",
    )
    convo_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default="{}",
    )

    __table_args__ = (
        CheckConstraint(
            f"channel IN ({', '.join(repr(c) for c in CONV_CHANNELS)})",
            name="channel_check",
        ),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in CONV_STATUSES)})",
            name="status_check",
        ),
        CheckConstraint(
            "outcome IS NULL OR outcome IN (" + ", ".join(repr(o) for o in CONV_OUTCOMES) + ")",
            name="outcome_check",
        ),
        Index("idx_conv_tenant_started", "tenant_id", "started_at"),
        Index("idx_conv_employee", "employee_id"),
        Index("idx_conv_status", "tenant_id", "status"),
        Index("idx_conv_end_user", "tenant_id", "end_user_pseudo_id"),
        Index(
            "idx_conv_idle",
            "status",
            "last_message_at",
            postgresql_where=text("status IN ('open', 'active', 'waiting_human')"),
        ),
    )
