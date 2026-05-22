"""Audit Service — emit AuditEvent.

依 MC-001 (Audit Service) + engineering-charter §1 (Governance-first)。

設計原則：
- append-only：本服務只 INSERT，DB trigger 會擋 UPDATE/DELETE
- 失敗時不靜默吞錯（否則 governance 失效）；caller 必須處理 exception
- payload 必須是 JSON-serializable dict
- tenant_id 可為 None（系統層級事件如 tenant 建立）

usage:
    async with session_scope(tenant_id=tid) as session:
        await audit.emit(
            session,
            event_type="tenant.created",
            tenant_id=tid,
            actor_id="system",
            resource_type="tenant",
            resource_id=str(tid),
            payload={"slug": "acme"},
        )
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog


async def emit(
    session: AsyncSession,
    *,
    event_type: str,
    tenant_id: uuid.UUID | None = None,
    actor_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> AuditLog:
    """寫一筆 AuditLog。

    Args:
        session: async session（由 caller 管理 transaction）
        event_type: e.g. "tenant.created" / "skill.promoted" / "ai.draft_generated"
        tenant_id: 該事件所屬 tenant；系統事件可為 None
        actor_id: 操作者識別（tenant admin id / api_key id / "system"）
        resource_type: 操作對象種類（"tenant" / "skill_version" / ...）
        resource_id: 操作對象識別
        payload: JSONB 任意 metadata

    Returns:
        新建的 AuditLog（id 已填）
    """
    entry = AuditLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        payload=payload or {},
    )
    session.add(entry)
    await session.flush()
    return entry
