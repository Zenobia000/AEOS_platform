"""Canary HTTP API integration tests."""

from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.tenant import Tenant


async def _seed_tenant(session: AsyncSession, suffix: str = "cn") -> Tenant:
    t = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}-{suffix}")
    session.add(t)
    await session.flush()
    return t


async def test_get_canary_default_zero(client: AsyncClient, webhook_session: AsyncSession) -> None:
    t = await _seed_tenant(webhook_session, "get")
    resp = await client.get(f"/api/v1/admin/canary/{t.id}")
    assert resp.status_code == 200
    assert resp.json()["canary_percent"] == 0


async def test_set_canary_25(client: AsyncClient, webhook_session: AsyncSession) -> None:
    t = await _seed_tenant(webhook_session, "25")
    resp = await client.post(
        f"/api/v1/admin/canary/{t.id}",
        json={
            "percent": 25,
            "actor_id": "cto",
            "reason": "pass rate raised",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["canary_percent"] == 25


async def test_set_canary_out_of_range_422(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    t = await _seed_tenant(webhook_session, "oor")
    resp = await client.post(
        f"/api/v1/admin/canary/{t.id}",
        json={"percent": 150, "actor_id": "x", "reason": "r"},
    )
    assert resp.status_code == 422


async def test_set_canary_same_409(client: AsyncClient, webhook_session: AsyncSession) -> None:
    t = await _seed_tenant(webhook_session, "same")
    await client.post(
        f"/api/v1/admin/canary/{t.id}",
        json={"percent": 30, "actor_id": "x", "reason": "r"},
    )
    resp = await client.post(
        f"/api/v1/admin/canary/{t.id}",
        json={"percent": 30, "actor_id": "x", "reason": "r2"},
    )
    assert resp.status_code == 409
