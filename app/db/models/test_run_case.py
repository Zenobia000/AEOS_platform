"""TestRunCase — 單一 case 在 single run 的執行結果 (composite PK)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base

TEST_RUN_CASE_STATUSES = ("pending", "running", "passed", "failed", "error")


class TestRunCase(Base):
    __tablename__ = "test_run_case"
    __test__ = False

    test_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("test_run.id", ondelete="CASCADE"),
        primary_key=True,
    )
    test_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("test_case.id", ondelete="CASCADE"),
        primary_key=True,
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="pending")
    actual_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    judge_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    judge_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in TEST_RUN_CASE_STATUSES)})",
            name="test_run_case_status_check",
        ),
    )
