"""ConversationHandoff — AI → 人 → AI 換手事件追蹤.

依 db-schema.md §4.6 + MC-010:
- 4 種 reason: low_confidence / restricted_tool / user_request / policy_deny
- to_conversation_id NULL 表示 expert 還沒接手；partial index 用於高頻查 pending
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base

HANDOFF_REASONS = (
    "low_confidence",
    "restricted_tool",
    "user_request",
    "policy_deny",
)


class ConversationHandoff(Base):
    __tablename__ = "conversation_handoff"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    from_conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversation.id"),
        nullable=False,
    )
    to_conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="NULL until Expert picks up",
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    handoff_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="context for Expert",
    )
    expert_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="who picked up",
    )
    picked_up_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
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
            f"reason IN ({', '.join(repr(r) for r in HANDOFF_REASONS)})",
            name="reason_check",
        ),
        Index(
            "idx_handoff_pending",
            "created_at",
            postgresql_where=text("to_conversation_id IS NULL"),
        ),
    )
