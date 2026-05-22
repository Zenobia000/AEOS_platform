"""AuditLog — append-only audit trail.

依 db-schema.md §1 命名 + §3.2 (audit_log 跨 tenant by design)
+ MC-001 (Audit Service) + engineering-charter 原則 1 (Governance-first)：
所有 AI 對外行為、tenant admin 操作、Skill lifecycle 變更必發 AuditEvent。

contract 規定：
- 單數表名（`audit_log`）
- 純 TEXT（無 VARCHAR(N)）
- BIGSERIAL PK：append-only 訊號（db-schema §1 line 23 例外條款）
- DB trigger 阻擋 UPDATE / DELETE（在 migration 中建）
- audit_log 是 cross-tenant by design：tenant_id 是資料欄位，
  不是 RLS 強制過濾（db-schema §3.2 / line 30）

對應 MC-001 §索引：
- ix on (tenant_id, occurred_at desc)
- ix on (event_type, occurred_at desc)
- ix on (resource_type, resource_id)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Index, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    actor_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="操作者：tenant admin user id / api_key id / 'system'",
    )
    event_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="e.g. tenant.created, skill.promoted, ai.draft_generated",
    )
    resource_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_audit_log_tenant_occurred", "tenant_id", "occurred_at"),
        Index("ix_audit_log_event_type", "event_type", "occurred_at"),
        Index("ix_audit_log_resource", "resource_type", "resource_id"),
    )
