"""OutboundMessage — 出站訊息投遞紀錄（retry + audit）.

依 db-schema.md §4.9 + MC-011 + API-002:
- 4 態 status: pending / sent / failed / retrying
- retry_count + error_message 支援重試邏輯
- partial index idx_outbound_pending 用於 worker 撿活
- conversation_id 強制 FK；message_id 邏輯 FK (message 複合 PK)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base

OUTBOUND_CHANNELS = ("line", "web_chat", "whatsapp")
OUTBOUND_STATUSES = (
    "pending",
    "sent",
    "failed",
    "retrying",
    "awaiting_review",  # Draft Mode：AI 產出後等 expert 審
    "rejected",  # Expert 拒絕；不 push
)


class OutboundMessage(Base):
    __tablename__ = "outbound_message"

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
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversation.id"),
        nullable=False,
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="internal message that triggered this — logical FK (message PK is composite)",
    )
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    channel_user_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="target user (hashed)",
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            f"channel IN ({', '.join(repr(c) for c in OUTBOUND_CHANNELS)})",
            name="channel_check",
        ),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in OUTBOUND_STATUSES)})",
            name="status_check",
        ),
        Index(
            "idx_outbound_pending",
            "status",
            "created_at",
            postgresql_where=text("status IN ('pending', 'retrying')"),
        ),
    )
