"""TestCase — 單一測試題 (S3 / AC-001)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, Text, func, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base


class TestCase(Base):
    __tablename__ = "test_case"
    __test__ = False  # 阻止 pytest 把 ORM model 當測試類別收集

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
    name: Mapped[str] = mapped_column(Text, nullable=False)
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    expected_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    expected_keywords: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default="{}",
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    skill_slug: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="vertical/skill scope; NULL = 通用題 (CR-0001 多 vertical)",
    )
    created_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("idx_test_case_tenant", "tenant_id", "enabled"),
        Index(
            "idx_test_case_skill_slug",
            "tenant_id",
            "skill_slug",
            postgresql_where=text("skill_slug IS NOT NULL"),
        ),
    )
