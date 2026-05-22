"""AuditLog append-only + AuditService 測試."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog
from app.services import audit


async def test_audit_emit_inserts(db_session: AsyncSession) -> None:
    """AuditService.emit 寫一筆 → 可查回."""
    tid = uuid.uuid4()
    entry = await audit.emit(
        db_session,
        event_type="tenant.created",
        tenant_id=tid,
        actor_id="system",
        resource_type="tenant",
        resource_id=str(tid),
        payload={"slug": "test"},
    )

    assert entry.id is not None
    assert entry.event_type == "tenant.created"
    assert entry.payload == {"slug": "test"}

    found = (await db_session.execute(select(AuditLog).where(AuditLog.id == entry.id))).scalar_one()
    assert found.actor_id == "system"
    assert found.tenant_id == tid


async def test_audit_with_null_tenant(db_session: AsyncSession) -> None:
    """系統事件 tenant_id=None 可寫入。"""
    entry = await audit.emit(
        db_session,
        event_type="system.startup",
        tenant_id=None,
        actor_id="system",
        payload={"version": "0.0.1"},
    )

    assert entry.id is not None
    assert entry.tenant_id is None


async def test_audit_log_blocks_update(db_session: AsyncSession) -> None:
    """UPDATE audit_log → trigger raise exception (append-only)."""
    entry = await audit.emit(
        db_session,
        event_type="test.event",
        tenant_id=uuid.uuid4(),
        payload={},
    )
    await db_session.flush()

    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text("UPDATE audit_log SET event_type = 'tampered' WHERE id = :id"),
            {"id": entry.id},
        )

    assert "append-only" in str(exc_info.value).lower()


async def test_audit_log_blocks_delete(db_session: AsyncSession) -> None:
    """DELETE audit_log → trigger raise exception (append-only)."""
    entry = await audit.emit(
        db_session,
        event_type="test.delete",
        tenant_id=uuid.uuid4(),
        payload={},
    )
    await db_session.flush()

    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text("DELETE FROM audit_log WHERE id = :id"),
            {"id": entry.id},
        )

    assert "append-only" in str(exc_info.value).lower()
