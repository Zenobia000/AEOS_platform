"""TestRun — 批次測試執行 (S3 / AC-001)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base

TEST_RUN_STATUSES = ("pending", "running", "completed", "failed")


class TestRun(Base):
    __tablename__ = "test_run"
    __test__ = False

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
    skill_slug: Mapped[str] = mapped_column(Text, nullable=False)
    skill_version: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="pending")
    total_cases: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    passed_cases: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    failed_cases: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    pass_rate: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in TEST_RUN_STATUSES)})",
            name="test_run_status_check",
        ),
        Index("idx_test_run_tenant", "tenant_id", "created_at"),
    )
