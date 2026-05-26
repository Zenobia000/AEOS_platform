"""SkillBinding — Employee ↔ SkillVersion 多對多綁定 + routing rule.

依 db-schema.md §3.3 + MC-005 + CR-0001:
- 一個 employee 可綁多個 skill_version（不同 vertical 並存）
- (employee_id, skill_version_id) unique — 同綁定不重複
- routing_rule JSONB — hybrid router (keyword / llm_intent / channel_match / explicit)
- is_default — 每 employee 至多 1 個 fallback skill（partial unique idx 守門）
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Index, Integer, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base


class SkillBinding(Base):
    __tablename__ = "skill_binding"

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
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employee.id"),
        nullable=False,
    )
    skill_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skill_version.id"),
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="ordering when employee has multiple skills",
    )
    routing_rule: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="hybrid router rule: {type, params, priority}; '{}' = match-all",
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
        comment="fallback skill when no routing_rule matches",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index(
            "idx_skill_binding_emp_sv",
            "employee_id",
            "skill_version_id",
            unique=True,
        ),
        Index(
            "uq_skill_binding_default_per_emp",
            "employee_id",
            unique=True,
            postgresql_where=text("is_default = true"),
        ),
    )
