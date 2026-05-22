"""async session + 基本 CRUD 冒煙測試."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.tenant import Tenant, TenantStatus


async def test_tenant_create_and_read(db_session: AsyncSession) -> None:
    """tenant 表可建立 + 讀取，預設 status = pending。"""
    tenant = Tenant(name="Acme Co", slug="acme")
    db_session.add(tenant)
    await db_session.flush()

    result = await db_session.execute(select(Tenant).where(Tenant.slug == "acme"))
    found = result.scalar_one()

    assert found.id == tenant.id
    assert found.name == "Acme Co"
    assert found.status == TenantStatus.pending
    assert found.created_at is not None


async def test_tenant_unique_slug(db_session: AsyncSession) -> None:
    """slug 重複應觸發 unique 約束。"""
    db_session.add(Tenant(name="First", slug="dup"))
    await db_session.flush()
    db_session.add(Tenant(name="Second", slug="dup"))

    import pytest
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await db_session.flush()
