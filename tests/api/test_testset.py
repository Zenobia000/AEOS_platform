"""TestSet HTTP API integration tests."""

from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.tenant import Tenant


async def _seed_tenant(session: AsyncSession, suffix: str = "ts") -> Tenant:
    t = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}-{suffix}")
    session.add(t)
    await session.flush()
    return t


async def test_create_and_list_cases(client: AsyncClient, webhook_session: AsyncSession) -> None:
    tenant = await _seed_tenant(webhook_session, "cl")

    create = await client.post(
        "/api/v1/testset/cases",
        json={
            "tenant_id": str(tenant.id),
            "name": "退貨期限",
            "user_input": "退貨多久",
            "expected_outcome": "7 天",
            "expected_keywords": ["7 天", "退貨"],
            "created_by": "expert-amy",
        },
    )
    assert create.status_code == 200
    case_id = create.json()["case_id"]

    listing = await client.get(f"/api/v1/testset/cases?tenant_id={tenant.id}")
    assert listing.status_code == 200
    body = listing.json()
    assert body["count"] == 1
    assert body["items"][0]["case_id"] == case_id
    assert body["items"][0]["expected_keywords"] == ["7 天", "退貨"]


async def test_create_case_blank_name_409(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    """min_length=1 通過 Pydantic（whitespace 算 1 char），但 service 層 strip 後拒絕 → 409."""
    tenant = await _seed_tenant(webhook_session, "val")
    resp = await client.post(
        "/api/v1/testset/cases",
        json={
            "tenant_id": str(tenant.id),
            "name": "   ",
            "user_input": "x",
            "expected_outcome": "y",
        },
    )
    assert resp.status_code == 409
    assert "name" in resp.json()["detail"]


async def test_create_case_empty_input_422(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    """完全空字串 → Pydantic 422."""
    tenant = await _seed_tenant(webhook_session, "val2")
    resp = await client.post(
        "/api/v1/testset/cases",
        json={
            "tenant_id": str(tenant.id),
            "name": "ok",
            "user_input": "",
            "expected_outcome": "y",
        },
    )
    assert resp.status_code == 422


async def test_disable_case(client: AsyncClient, webhook_session: AsyncSession) -> None:
    tenant = await _seed_tenant(webhook_session, "dis")
    create = await client.post(
        "/api/v1/testset/cases",
        json={
            "tenant_id": str(tenant.id),
            "name": "a",
            "user_input": "x",
            "expected_outcome": "y",
        },
    )
    case_id = create.json()["case_id"]
    disable = await client.post(f"/api/v1/testset/cases/{case_id}/disable")
    assert disable.status_code == 200
    assert disable.json()["enabled"] is False

    listing = await client.get(f"/api/v1/testset/cases?tenant_id={tenant.id}")
    assert listing.json()["count"] == 0


async def test_create_run_without_cases_409(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    tenant = await _seed_tenant(webhook_session, "norun")
    resp = await client.post(
        "/api/v1/testset/runs",
        json={
            "tenant_id": str(tenant.id),
            "skill_slug": "customer-service/faq-respond",
            "skill_version": "v1.0.0",
        },
    )
    assert resp.status_code == 409


async def test_create_run_and_get_summary(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    tenant = await _seed_tenant(webhook_session, "run")
    await client.post(
        "/api/v1/testset/cases",
        json={
            "tenant_id": str(tenant.id),
            "name": "a",
            "user_input": "x",
            "expected_outcome": "y",
        },
    )
    create = await client.post(
        "/api/v1/testset/runs",
        json={
            "tenant_id": str(tenant.id),
            "skill_slug": "customer-service/faq-respond",
            "skill_version": "v1.0.0",
        },
    )
    assert create.status_code == 200
    run_id = create.json()["run_id"]
    assert create.json()["status"] == "pending"
    assert create.json()["total_cases"] == 1

    summary = await client.get(f"/api/v1/testset/runs/{run_id}")
    assert summary.status_code == 200
    assert summary.json()["status"] == "pending"

    cases = await client.get(f"/api/v1/testset/runs/{run_id}/cases")
    assert cases.status_code == 200
    assert cases.json()["count"] == 1
    assert cases.json()["items"][0]["status"] == "pending"


async def test_get_unknown_run_404(client: AsyncClient, webhook_session: AsyncSession) -> None:
    resp = await client.get(f"/api/v1/testset/runs/{uuid.uuid4()}")
    assert resp.status_code == 404
