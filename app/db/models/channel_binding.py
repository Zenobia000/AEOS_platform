"""ChannelBinding — Employee ↔ channel (e.g. LINE OA) 綁定.

依 db-schema.md §4.7 + MC-011:
- 3 種 channel: line / web_chat / whatsapp (Phase 1 只 line live)
- config JSONB 載加密 credentials (LINE channel secret / access token)
- (employee_id, channel) unique — 一個 employee 一個 channel 只能綁一次
- Phase 1 透過 employee FK ON DELETE CASCADE 隨 employee 一起刪
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base

CHANNELS = ("line", "web_chat", "whatsapp")


class ChannelBinding(Base):
    __tablename__ = "channel_binding"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employee.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="encrypted channel credentials",
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            f"channel IN ({', '.join(repr(c) for c in CHANNELS)})",
            name="channel_check",
        ),
        Index(
            "idx_channel_binding_emp_chan",
            "employee_id",
            "channel",
            unique=True,
        ),
    )
