"""Admin API integration tests — kill switch endpoints."""

from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.tenant import Tenant


async def _seed_tenant(session: AsyncSession, suffix: str = "ad") -> Tenant:
    tenant = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}-{suffix}")
    session.add(tenant)
    await session.flush()
    return tenant


async def test_get_kill_switch_default_enabled(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    tenant = await _seed_tenant(webhook_session, "get-default")
    resp = await client.get(f"/api/v1/admin/kill-switch/{tenant.id}")
    assert resp.status_code == 200
    assert resp.json()["ai_enabled"] is True


async def test_disable_then_get(client: AsyncClient, webhook_session: AsyncSession) -> None:
    tenant = await _seed_tenant(webhook_session, "dis-then-get")
    resp = await client.post(
        f"/api/v1/admin/kill-switch/{tenant.id}/disable",
        json={
            "confirm_tenant_id": str(tenant.id),
            "actor_id": "cto",
            "reason": "incident",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["ai_enabled"] is False

    resp2 = await client.get(f"/api/v1/admin/kill-switch/{tenant.id}")
    assert resp2.json()["ai_enabled"] is False
    assert resp2.json()["disabled_by"] == "cto"


async def test_disable_confirm_mismatch_409(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    tenant = await _seed_tenant(webhook_session, "mismatch-api")
    resp = await client.post(
        f"/api/v1/admin/kill-switch/{tenant.id}/disable",
        json={
            "confirm_tenant_id": str(uuid.uuid4()),
            "actor_id": "x",
            "reason": "r",
        },
    )
    assert resp.status_code == 409
    assert "mismatch" in resp.json()["detail"]


async def test_enable_after_disable(client: AsyncClient, webhook_session: AsyncSession) -> None:
    tenant = await _seed_tenant(webhook_session, "enable-flow")
    await client.post(
        f"/api/v1/admin/kill-switch/{tenant.id}/disable",
        json={
            "confirm_tenant_id": str(tenant.id),
            "actor_id": "x",
            "reason": "r",
        },
    )
    resp = await client.post(
        f"/api/v1/admin/kill-switch/{tenant.id}/enable",
        json={"actor_id": "cto", "reason": "resolved"},
    )
    assert resp.status_code == 200
    assert resp.json()["ai_enabled"] is True


async def test_disable_empty_reason_422(client: AsyncClient, webhook_session: AsyncSession) -> None:
    tenant = await _seed_tenant(webhook_session, "empty-reason")
    resp = await client.post(
        f"/api/v1/admin/kill-switch/{tenant.id}/disable",
        json={
            "confirm_tenant_id": str(tenant.id),
            "actor_id": "x",
            "reason": "",
        },
    )
    assert resp.status_code == 422
