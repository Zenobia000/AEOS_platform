"""ToolInvocation — 每次 tool call 的 append-only 紀錄.

依 db-schema.md §3.5 + MC-006:
- 4 態 status: success / error / timeout / rejected_by_policy
- input / output 都 PII-masked（依 ADR-0005）
- policy_decision JSONB 記錄 policy engine 的判斷結果（規則 / 原因）
- message_id 邏輯指向 message 表（partitioned，PK 為 (id, created_at)），不設 FK
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base

TOOL_INVOCATION_STATUSES = (
    "success",
    "error",
    "timeout",
    "rejected_by_policy",
)


class ToolInvocation(Base):
    __tablename__ = "tool_invocation"

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
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="logical FK conversation(id)",
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="logical FK message — message PK 是複合鍵 (id, created_at)，不設 DB FK",
    )
    tool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tool.id"),
        nullable=False,
    )
    employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="logical FK employee(id)",
    )
    skill_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="which Skill triggered this call",
    )
    input: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="PII-masked",
    )
    output: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="PII-masked; NULL on error",
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_token: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="LLM token cost (if applicable)",
    )
    policy_decision: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment='{ "allowed": true, "rule": "rule-003", "reason": "..." }',
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in TOOL_INVOCATION_STATUSES)})",
            name="status_check",
        ),
        Index("idx_tool_invocation_tenant_time", "tenant_id", "created_at"),
        Index("idx_tool_invocation_tool", "tool_id", "created_at"),
        Index("idx_tool_invocation_conv", "conversation_id"),
    )
