"""Skill — 可版本化的 AI 能力資產 (aggregate root for SkillVersion).

依 db-schema.md §3.1 + MC-005 (Skill Registry) + ADR-0003:
- Git monorepo 是 source of truth；DB 為查詢鏡像
- tenant_id 可為 NULL（platform-level skill，Phase 2）；Phase 1 全為 per-tenant
- slug 格式：'vertical/skill-name' (e.g. 'customer-service/faq-respond')
- current_production_version 指向目前 prod 用的 semver
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base


class Skill(Base):
    __tablename__ = "skill"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant.id"),
        nullable=True,
        comment="NULL = platform-level skill (Phase 2)",
    )
    slug: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="'customer-service/faq-respond'",
    )
    vertical: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="'customer-service'",
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_production_version: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="semver, e.g. '1.2.0'",
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
