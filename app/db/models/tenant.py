"""Tenant aggregate root.

依 db-schema.md §1 命名 + §3 + MC-004 (Tenant Manager) + ADR-0007 (multi-tenant).

contract 規定（db-schema.md line 22-25）：
- 單數表名（`tenant`，非 `tenants`）
- 純 TEXT，無 VARCHAR(N)
- String enum 用 TEXT + CHECK constraint，不用 PG native enum

Phase 1 採共享 PG + RLS；本表的 tenant.id (UUID) 是所有其他表
RLS policy 的 `current_setting('app.tenant_id')::uuid` 比對對象。
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.api_key import ApiKey


class TenantStatus(enum.StrEnum):
    """MC-004 §狀態機 4 態（與 DB CHECK constraint 同步）。"""

    pending = "pending"
    active = "active"
    suspended = "suspended"
    archived = "archived"


_STATUS_VALUES = ", ".join(f"'{s.value}'" for s in TenantStatus)


class Tenant(Base):
    __tablename__ = "tenant"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="pending",
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

    api_keys: Mapped[list[ApiKey]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            f"status IN ({_STATUS_VALUES})",
            name="status_check",
        ),
    )
