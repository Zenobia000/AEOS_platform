"""SkillVersion — 單個 Skill 的某個版本快照.

依 db-schema.md §3.2 + MC-005:
- 5 態 status: draft / testing / approved / production / deprecated
- prompt_template_ref + test_set_ref + git_commit_sha 都指向 git 中的具體檔案
- production 狀態額外 CHECK：必須有 approved_by + approved_at + pass_rate ≥ 0.80
  （這個 CHECK constraint 直接落地 MC-005 Quality Gate 的最後一層）
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base

SKILL_VERSION_STATUSES = (
    "draft",
    "testing",
    "approved",
    "production",
    "deprecated",
)


class SkillVersion(Base):
    __tablename__ = "skill_version"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skill.id"),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant.id"),
        nullable=True,
        comment="redundant, for query speed; NULL follows skill.tenant_id",
    )
    version: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="semver",
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="draft",
    )
    prompt_template_ref: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="git path: 'skills/cs/faq/prompt/v1.0.0.md'",
    )
    io_contract: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="input/output JSON Schema",
    )
    tool_bindings: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default="{}",
        comment="tool slugs this skill can use",
    )
    policy_refs: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default="{}",
        comment="policy IDs",
    )
    test_set_ref: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="git path to test cases",
    )
    test_pass_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="0.0000 ~ 1.0000",
    )
    quality_gate_scores: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment='{ "pass_rate": 0.85, "latency_p95_ms": 1200, ... }',
    )
    approved_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deployed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    git_commit_sha: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="corresponding git commit (40 chars)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("skill_id", "version", name="uq_skill_version_skill_version"),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in SKILL_VERSION_STATUSES)})",
            name="status_check",
        ),
        # MC-005 Quality Gate: production 版本必須有 approver + pass_rate >= 0.80
        CheckConstraint(
            "(status <> 'production') OR "
            "(approved_by IS NOT NULL AND approved_at IS NOT NULL "
            "AND test_pass_rate >= 0.80)",
            name="production_quality_gate",
        ),
        Index("idx_skill_version_skill_version", "skill_id", "version"),
        Index("idx_skill_version_tenant_status", "tenant_id", "status"),
    )
