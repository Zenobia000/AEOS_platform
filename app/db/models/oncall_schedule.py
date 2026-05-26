"""OncallSchedule — 第 25 張表 (Phase 1 後續 #17).

對應 PRD-001 §5.5 + RUNBOOK-001 + SEC-001 §6.1 #12 incident drill。
Phase 1：手動維護；Phase 2 接 PagerDuty schedule sync。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base


class OncallSchedule(Base):
    __tablename__ = "oncall_schedule"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
    )
    shift_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    shift_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    primary_expert_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    secondary_expert_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    pagerduty_schedule_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
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
            "shift_end > shift_start",
            name="oncall_schedule_time_range_check",
        ),
        Index(
            "idx_oncall_schedule_tenant_shift",
            "tenant_id",
            "shift_start",
            "shift_end",
        ),
    )
