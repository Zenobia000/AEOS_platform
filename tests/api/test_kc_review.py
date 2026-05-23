"""KC Review HTTP API integration tests."""

from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.knowledge_card import KnowledgeCard
from app.db.models.tenant import Tenant


async def _seed_draft(
    session: AsyncSession,
    *,
    slug_suffix: str = "kc",
) -> tuple[Tenant, KnowledgeCard]:
    tenant = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}-{slug_suffix}")
    session.add(tenant)
    await session.flush()
    kc = KnowledgeCard(
        tenant_id=tenant.id,
        card_type="policy",
        title="退貨政策",
        body_markdown="本店退貨期限為到貨後 7 天內",
        tags=["退貨"],
        status="draft",
    )
    session.add(kc)
    await session.flush()
    return tenant, kc


async def test_api_list_drafts(client: AsyncClient, webhook_session: AsyncSession) -> None:
    await _seed_draft(webhook_session, slug_suffix="api-list")
    resp = await client.get("/api/v1/kc/drafts")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1
    assert body["items"][0]["title"] == "退貨政策"


async def test_api_approve(client: AsyncClient, webhook_session: AsyncSession) -> None:
    _, kc = await _seed_draft(webhook_session, slug_suffix="api-appv")
    resp = await client.post(
        f"/api/v1/kc/drafts/{kc.id}/approve",
        json={"expert_id": "x"},
    )
    assert resp.status_code == 200
    assert resp.json()["new_status"] == "approved"


async def test_api_edit(client: AsyncClient, webhook_session: AsyncSession) -> None:
    _, kc = await _seed_draft(webhook_session, slug_suffix="api-edit")
    resp = await client.post(
        f"/api/v1/kc/drafts/{kc.id}/edit",
        json={
            "expert_id": "x",
            "title": "退貨政策（修訂）",
            "tags": ["退貨", "政策"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["new_status"] == "approved"


async def test_api_archive(client: AsyncClient, webhook_session: AsyncSession) -> None:
    _, kc = await _seed_draft(webhook_session, slug_suffix="api-arch")
    resp = await client.post(
        f"/api/v1/kc/drafts/{kc.id}/archive",
        json={"expert_id": "x", "reason": "重複"},
    )
    assert resp.status_code == 200
    assert resp.json()["new_status"] == "archived"


async def test_api_approve_409_for_non_draft(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    _, kc = await _seed_draft(webhook_session, slug_suffix="api-409")
    kc.status = "approved"
    await webhook_session.flush()

    resp = await client.post(
        f"/api/v1/kc/drafts/{kc.id}/approve",
        json={"expert_id": "x"},
    )
    assert resp.status_code == 409


async def test_api_validation_empty_expert_id(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    _, kc = await _seed_draft(webhook_session, slug_suffix="api-val")
    resp = await client.post(
        f"/api/v1/kc/drafts/{kc.id}/approve",
        json={"expert_id": ""},
    )
    assert resp.status_code == 422
