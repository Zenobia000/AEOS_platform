"""Employee — AI 員工 aggregate root.

依 db-schema.md §4.1 + MC-009 (Employee Runtime):
- Phase 1 唯一 role: customer_service
- 4 態 status: draft / live / paused / retired
- runtime_snapshot 是 Frozen Runtime（engineering-charter 原則 2）的具體實作 —
  conversation 開始時把 employee.runtime_snapshot 釘住，整段對話不會因
  employee config 變更而改變行為
- persona_config / runtime_snapshot 為 JSONB
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base

EMPLOYEE_STATUSES = ("draft", "live", "paused", "retired")


class Employee(Base):
    __tablename__ = "employee"

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
    name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="'customer_service' (Phase 1)",
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="semver snapshot",
    )
    persona_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="{ tone, style, language, greeting }",
    )
    runtime_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="frozen config: skill_bindings, tool_bindings, llm_config",
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
            f"status IN ({', '.join(repr(s) for s in EMPLOYEE_STATUSES)})",
            name="status_check",
        ),
        Index("idx_employee_tenant", "tenant_id"),
        Index("idx_employee_status", "tenant_id", "status"),
    )
