"""ApiKey — 客戶端 API 認證憑證.

依 db-schema.md §1 命名 + ADR-0006 (Auth)：
- Tenant Admin 用 Email+Password+MFA；
- 本表是「程式對程式」的 API Key（bcrypt hash），用於 web/SPA → API、
  internal worker → API 等場景

contract 規定：單數表名 + 純 TEXT。

RLS：本表 enable RLS，policy: tenant_id = current_setting('app.tenant_id')::uuid
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.tenant import Tenant


class ApiKey(Base):
    __tablename__ = "api_key"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    key_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    last_four: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    tenant: Mapped[Tenant] = relationship(back_populates="api_keys")
