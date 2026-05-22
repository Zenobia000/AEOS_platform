"""Message — 對話中的單則訊息（按月分割 append-only）.

依 db-schema.md §4.5 + MC-010 (Conversation Engine):
- PARTITION BY RANGE (created_at)，每月一個 partition
- 複合 PK (id, created_at) — partition 要求 PK 必含 partition key
- UNIQUE (conversation_id, seq, created_at) — 序號去重
- FK conversation_id 邏輯指向 conversation(id)，但 PG 不允許 partitioned
  table 對外鍵反向支援 —— 由應用層保證一致
- content 為 pseudonymized；原文若需保留可指向 encrypted_pii(id)
- role 限 user / assistant / tool / system
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Integer,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base

MESSAGE_ROLES = ("user", "assistant", "tool", "system")


class Message(Base):
    __tablename__ = "message"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        server_default=func.gen_random_uuid(),
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="logical FK conversation(id) — not enforced across partitions",
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="pseudonymized",
    )
    content_raw_ref: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="FK encrypted_pii(id) if PII vault is used",
    )
    skill_invocation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    tool_invocations: Mapped[list[Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
    )
    token_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="for context window budget tracking",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        PrimaryKeyConstraint("id", "created_at", name="pk_message"),
        UniqueConstraint(
            "conversation_id",
            "seq",
            "created_at",
            name="uq_message_conv_seq",
        ),
        CheckConstraint(
            f"role IN ({', '.join(repr(r) for r in MESSAGE_ROLES)})",
            name="role_check",
        ),
        {
            "postgresql_partition_by": "RANGE (created_at)",
        },
    )
