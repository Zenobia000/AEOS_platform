"""Tool — AI 員工可呼叫的外部能力 (aggregate root for ToolInvocation).

依 db-schema.md §3.4 + MC-006:
- 4 種 tool_type: internal / http_api / db_query / function
- 5 種 auth_method: none / api_key / bearer / basic / hmac
- 3 級 risk_tier: safe / caution / restricted（policy engine 用於分級攔截）
- input_schema / output_schema 為 JSON Schema，給 LLM function calling 用
- rate_limit / timeout / retry 都在 DB 層集中管理
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base

TOOL_TYPES = ("internal", "http_api", "db_query", "function")
TOOL_AUTH_METHODS = ("none", "api_key", "bearer", "basic", "hmac")
TOOL_RISK_TIERS = ("safe", "caution", "restricted")


class Tool(Base):
    __tablename__ = "tool"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant.id"),
        nullable=True,
        comment="NULL = system built-in tool",
    )
    slug: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="'search_knowledge', 'lookup_order'",
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="LLM-facing description (function calling)",
    )
    tool_type: Mapped[str] = mapped_column(Text, nullable=False)
    endpoint: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="HTTP endpoint (when tool_type = 'http_api')",
    )
    auth_method: Mapped[str | None] = mapped_column(Text, nullable=True)
    auth_config: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="encrypted auth settings (key/token/secret)",
    )
    input_schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="JSON Schema for input",
    )
    output_schema: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="JSON Schema for output",
    )
    risk_tier: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="safe",
    )
    rate_limit_rpm: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="60",
        comment="requests per minute per tenant",
    )
    timeout_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="5000",
    )
    retry_policy: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default='{"max_retries": 2, "backoff_ms": 500}',
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
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

    __table_args__ = (
        CheckConstraint(
            f"tool_type IN ({', '.join(repr(t) for t in TOOL_TYPES)})",
            name="tool_type_check",
        ),
        CheckConstraint(
            "auth_method IS NULL OR auth_method IN ("
            + ", ".join(repr(a) for a in TOOL_AUTH_METHODS)
            + ")",
            name="auth_method_check",
        ),
        CheckConstraint(
            f"risk_tier IN ({', '.join(repr(r) for r in TOOL_RISK_TIERS)})",
            name="risk_tier_check",
        ),
    )
