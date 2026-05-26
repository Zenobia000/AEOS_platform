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


# ── CR-0001 #6: skill binding admin API ────────────────


async def _seed_skill_chain(
    session: AsyncSession,
    tenant: Tenant,
    *,
    slug: str = "customer-service/faq-respond",
    vertical: str = "customer-service",
    version: str = "1.0.0",
):
    """建 skill + skill_version + employee 用於 binding API 測試。"""
    from app.db.models.employee import Employee
    from app.db.models.skill import Skill
    from app.db.models.skill_version import SkillVersion

    skill = Skill(
        tenant_id=tenant.id,
        slug=slug,
        vertical=vertical,
        name="X",
    )
    session.add(skill)
    await session.flush()
    sv = SkillVersion(
        skill_id=skill.id,
        tenant_id=tenant.id,
        version=version,
        prompt_template_ref="x",
    )
    session.add(sv)
    emp = Employee(
        tenant_id=tenant.id,
        name="AI",
        role="customer_service",
        status="draft",
        version="1.0.0",
    )
    session.add(emp)
    await session.flush()
    return skill, sv, emp


async def test_list_tenant_skills_empty(client: AsyncClient, webhook_session: AsyncSession) -> None:
    tenant = await _seed_tenant(webhook_session, "sk-empty")
    resp = await client.get(f"/api/v1/admin/skills/{tenant.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["skills"] == []
    assert body["bindings"] == []


async def test_list_tenant_skills_with_binding(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    tenant = await _seed_tenant(webhook_session, "sk-with")
    _skill, sv, emp = await _seed_skill_chain(webhook_session, tenant)

    # 建 binding via API
    resp = await client.post(
        "/api/v1/admin/skills/bindings",
        json={
            "tenant_id": str(tenant.id),
            "employee_id": str(emp.id),
            "skill_version_id": str(sv.id),
            "routing_rule": {"type": "keyword", "params": {"keywords": ["test"]}, "priority": 10},
            "is_default": True,
            "priority": 0,
        },
    )
    assert resp.status_code == 200
    binding_data = resp.json()
    assert binding_data["is_default"] is True
    assert binding_data["routing_rule"]["type"] == "keyword"

    # list
    resp_list = await client.get(f"/api/v1/admin/skills/{tenant.id}")
    body = resp_list.json()
    assert len(body["skills"]) == 1
    assert len(body["bindings"]) == 1
    assert body["bindings"][0]["is_default"] is True


async def test_skill_binding_upsert(client: AsyncClient, webhook_session: AsyncSession) -> None:
    """同 (employee_id, skill_version_id) 第二次 POST 應更新而非新增."""
    tenant = await _seed_tenant(webhook_session, "sk-upsert")
    _skill, sv, emp = await _seed_skill_chain(webhook_session, tenant)

    base = {
        "tenant_id": str(tenant.id),
        "employee_id": str(emp.id),
        "skill_version_id": str(sv.id),
    }
    resp1 = await client.post(
        "/api/v1/admin/skills/bindings",
        json={**base, "routing_rule": {"type": "keyword"}, "priority": 5},
    )
    bid_1 = resp1.json()["id"]

    resp2 = await client.post(
        "/api/v1/admin/skills/bindings",
        json={**base, "routing_rule": {"type": "explicit"}, "priority": 99},
    )
    assert resp2.json()["id"] == bid_1  # 同 id → upsert
    assert resp2.json()["routing_rule"]["type"] == "explicit"
    assert resp2.json()["priority"] == 99


async def test_skill_binding_delete(client: AsyncClient, webhook_session: AsyncSession) -> None:
    tenant = await _seed_tenant(webhook_session, "sk-del")
    _skill, sv, emp = await _seed_skill_chain(webhook_session, tenant)
    resp = await client.post(
        "/api/v1/admin/skills/bindings",
        json={
            "tenant_id": str(tenant.id),
            "employee_id": str(emp.id),
            "skill_version_id": str(sv.id),
        },
    )
    bid = resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/admin/skills/bindings/{bid}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] == bid

    # 404 on second delete
    del_resp2 = await client.delete(f"/api/v1/admin/skills/bindings/{bid}")
    assert del_resp2.status_code == 404


async def test_route_preview_keyword_match(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    tenant = await _seed_tenant(webhook_session, "sk-preview")
    _skill, sv, emp = await _seed_skill_chain(
        webhook_session, tenant, slug="hr/leave-request", vertical="hr"
    )
    await client.post(
        "/api/v1/admin/skills/bindings",
        json={
            "tenant_id": str(tenant.id),
            "employee_id": str(emp.id),
            "skill_version_id": str(sv.id),
            "routing_rule": {
                "type": "keyword",
                "params": {"keywords": ["請假"]},
                "priority": 10,
            },
            "is_default": True,
        },
    )

    resp = await client.post(
        "/api/v1/admin/skills/route-preview",
        json={
            "employee_id": str(emp.id),
            "tenant_id": str(tenant.id),
            "message": "我想請假",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["matched_rule_type"] == "keyword"
    assert body["skill_slug"] == "hr/leave-request"
    assert body["skill_version_str"] == "v1.0.0"  # normalized for loader


async def test_route_preview_no_binding_422(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    tenant = await _seed_tenant(webhook_session, "sk-noemp")
    from app.db.models.employee import Employee

    emp = Employee(
        tenant_id=tenant.id,
        name="AI",
        role="customer_service",
        status="draft",
        version="1.0.0",
    )
    webhook_session.add(emp)
    await webhook_session.flush()

    resp = await client.post(
        "/api/v1/admin/skills/route-preview",
        json={
            "employee_id": str(emp.id),
            "tenant_id": str(tenant.id),
            "message": "hello",
        },
    )
    assert resp.status_code == 422
    assert "no skill bound" in resp.json()["detail"]
