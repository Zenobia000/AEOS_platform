"""TenantSetting — per-tenant kill switch + 治理開關 (S5).

對應 PRD-001 §5.5 + UF-004 emergency kill switch:
- ai_enabled = false → DraftProcessor 不呼叫 LLM；走 expert handoff
- 30 秒生效（無 cache；每 turn 查 DB；單筆 SELECT 成本 < 1ms）
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base


class TenantSetting(Base):
    __tablename__ = "tenant_setting"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant.id", ondelete="CASCADE"),
        primary_key=True,
    )
    ai_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disabled_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    disable_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    canary_percent: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "canary_percent >= 0 AND canary_percent <= 100",
            name="tenant_setting_canary_percent_check",
        ),
    )
