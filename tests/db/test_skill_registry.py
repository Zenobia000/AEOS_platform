"""MC-005 Skill Registry 測試 — skill / skill_version / skill_binding."""

from __future__ import annotations

from datetime import UTC
from decimal import Decimal

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.employee import Employee
from app.db.models.skill import Skill
from app.db.models.skill_binding import SkillBinding
from app.db.models.skill_version import SkillVersion
from app.db.models.tenant import Tenant


async def _make_tenant(session: AsyncSession, slug: str) -> Tenant:
    t = Tenant(name=f"T-{slug}", slug=slug)
    session.add(t)
    await session.flush()
    return t


async def _make_skill(session: AsyncSession, tenant: Tenant) -> Skill:
    s = Skill(
        tenant_id=tenant.id,
        slug="customer-service/faq-respond",
        vertical="customer-service",
        name="FAQ Responder",
        description="Phase 1 唯一 skill",
    )
    session.add(s)
    await session.flush()
    return s


# ── Skill ───────────────────────────────────────────


async def test_skill_create(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "sk-create")
    skill = await _make_skill(db_session, tenant)

    assert skill.id is not None
    assert skill.current_production_version is None
    assert skill.vertical == "customer-service"


async def test_skill_unique_slug_per_tenant(db_session: AsyncSession) -> None:
    """同一 tenant 不能有兩個相同 slug 的 skill（partial unique index COALESCE）."""
    tenant = await _make_tenant(db_session, "sk-uniq")
    await _make_skill(db_session, tenant)

    duplicate = Skill(
        tenant_id=tenant.id,
        slug="customer-service/faq-respond",
        vertical="customer-service",
        name="dup",
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        await db_session.flush()


# ── SkillVersion ────────────────────────────────────


async def test_skill_version_create_draft(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "sv-draft")
    skill = await _make_skill(db_session, tenant)
    sv = SkillVersion(
        skill_id=skill.id,
        tenant_id=tenant.id,
        version="1.0.0",
        prompt_template_ref="skills/cs/faq/prompt/v1.0.0.md",
    )
    db_session.add(sv)
    await db_session.flush()

    assert sv.id is not None
    assert sv.status == "draft"
    assert sv.tool_bindings == []
    assert sv.policy_refs == []


async def test_skill_version_unique_skill_version(db_session: AsyncSession) -> None:
    """(skill_id, version) unique。"""
    tenant = await _make_tenant(db_session, "sv-uniq")
    skill = await _make_skill(db_session, tenant)
    sv1 = SkillVersion(
        skill_id=skill.id,
        tenant_id=tenant.id,
        version="1.0.0",
        prompt_template_ref="x",
    )
    db_session.add(sv1)
    await db_session.flush()

    sv2 = SkillVersion(
        skill_id=skill.id,
        tenant_id=tenant.id,
        version="1.0.0",
        prompt_template_ref="x",
    )
    db_session.add(sv2)
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_skill_version_production_quality_gate(db_session: AsyncSession) -> None:
    """production status 需要 approver + pass_rate >= 0.80（DB CHECK 直接落地 MC-005 QG）."""
    tenant = await _make_tenant(db_session, "sv-prod-fail")
    skill = await _make_skill(db_session, tenant)

    # pass_rate 不足 → CHECK 阻擋
    bad = SkillVersion(
        skill_id=skill.id,
        tenant_id=tenant.id,
        version="1.0.0",
        prompt_template_ref="x",
        status="production",
        approved_by="user-1",
        approved_at=None,  # 缺 approved_at
        test_pass_rate=Decimal("0.50"),
    )
    db_session.add(bad)
    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()
    assert "production_quality_gate" in str(exc.value).lower()


async def test_skill_version_production_allowed(db_session: AsyncSession) -> None:
    """approver + pass_rate >= 0.80 → 可進 production."""
    from datetime import datetime

    tenant = await _make_tenant(db_session, "sv-prod-ok")
    skill = await _make_skill(db_session, tenant)

    sv = SkillVersion(
        skill_id=skill.id,
        tenant_id=tenant.id,
        version="1.0.0",
        prompt_template_ref="x",
        status="production",
        approved_by="expert-jenny",
        approved_at=datetime.now(UTC),
        test_pass_rate=Decimal("0.85"),
    )
    db_session.add(sv)
    await db_session.flush()
    assert sv.id is not None


async def test_skill_version_status_check(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "sv-bad-status")
    skill = await _make_skill(db_session, tenant)
    sv = SkillVersion(
        skill_id=skill.id,
        tenant_id=tenant.id,
        version="1.0.0",
        prompt_template_ref="x",
        status="weird_status",
    )
    db_session.add(sv)
    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()
    assert "status_check" in str(exc.value).lower()


async def test_skill_version_tool_bindings_array(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "sv-tools")
    skill = await _make_skill(db_session, tenant)
    sv = SkillVersion(
        skill_id=skill.id,
        tenant_id=tenant.id,
        version="1.0.0",
        prompt_template_ref="x",
        tool_bindings=["search_knowledge", "lookup_order"],
        policy_refs=["policy-001", "policy-002"],
    )
    db_session.add(sv)
    await db_session.flush()

    fetched = (
        await db_session.execute(select(SkillVersion).where(SkillVersion.id == sv.id))
    ).scalar_one()
    assert fetched.tool_bindings == ["search_knowledge", "lookup_order"]
    assert fetched.policy_refs == ["policy-001", "policy-002"]


# ── SkillBinding ────────────────────────────────────


async def test_skill_binding_create(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "sb-create")
    skill = await _make_skill(db_session, tenant)
    sv = SkillVersion(
        skill_id=skill.id,
        tenant_id=tenant.id,
        version="1.0.0",
        prompt_template_ref="x",
    )
    db_session.add(sv)
    emp = Employee(
        tenant_id=tenant.id,
        name="AI 客服",
        role="customer_service",
        status="draft",
        version="1.0.0",
    )
    db_session.add(emp)
    await db_session.flush()

    binding = SkillBinding(
        tenant_id=tenant.id,
        employee_id=emp.id,
        skill_version_id=sv.id,
        priority=10,
    )
    db_session.add(binding)
    await db_session.flush()

    assert binding.id is not None
    assert binding.priority == 10


async def test_skill_binding_unique_employee_version(db_session: AsyncSession) -> None:
    """同 employee 不可重複綁同個 skill_version."""
    tenant = await _make_tenant(db_session, "sb-uniq")
    skill = await _make_skill(db_session, tenant)
    sv = SkillVersion(
        skill_id=skill.id,
        tenant_id=tenant.id,
        version="1.0.0",
        prompt_template_ref="x",
    )
    db_session.add(sv)
    emp = Employee(
        tenant_id=tenant.id,
        name="AI",
        role="customer_service",
        status="draft",
        version="1.0.0",
    )
    db_session.add(emp)
    await db_session.flush()

    db_session.add(SkillBinding(tenant_id=tenant.id, employee_id=emp.id, skill_version_id=sv.id))
    await db_session.flush()
    db_session.add(SkillBinding(tenant_id=tenant.id, employee_id=emp.id, skill_version_id=sv.id))
    with pytest.raises(IntegrityError):
        await db_session.flush()


# ── CR-0001: routing_rule + is_default ──────────────


async def test_skill_binding_routing_rule_default(db_session: AsyncSession) -> None:
    """新建 binding 不指定 routing_rule 時應為空 dict {} 與 is_default=False."""
    tenant = await _make_tenant(db_session, "sb-rr-default")
    skill = await _make_skill(db_session, tenant)
    sv = SkillVersion(
        skill_id=skill.id, tenant_id=tenant.id, version="1.0.0", prompt_template_ref="x"
    )
    db_session.add(sv)
    emp = Employee(
        tenant_id=tenant.id,
        name="AI",
        role="customer_service",
        status="draft",
        version="1.0.0",
    )
    db_session.add(emp)
    await db_session.flush()

    binding = SkillBinding(tenant_id=tenant.id, employee_id=emp.id, skill_version_id=sv.id)
    db_session.add(binding)
    await db_session.flush()
    await db_session.refresh(binding)

    assert binding.routing_rule == {}
    assert binding.is_default is False


async def test_skill_binding_is_default_partial_unique(db_session: AsyncSession) -> None:
    """同 employee 至多 1 個 is_default=True（partial unique idx 守門）."""
    tenant = await _make_tenant(db_session, "sb-default-uniq")
    skill = await _make_skill(db_session, tenant)
    sv1 = SkillVersion(
        skill_id=skill.id, tenant_id=tenant.id, version="1.0.0", prompt_template_ref="x"
    )
    sv2 = SkillVersion(
        skill_id=skill.id, tenant_id=tenant.id, version="1.1.0", prompt_template_ref="x"
    )
    db_session.add_all([sv1, sv2])
    emp = Employee(
        tenant_id=tenant.id,
        name="AI",
        role="customer_service",
        status="draft",
        version="1.0.0",
    )
    db_session.add(emp)
    await db_session.flush()

    # 第 1 個 default — OK
    db_session.add(
        SkillBinding(
            tenant_id=tenant.id,
            employee_id=emp.id,
            skill_version_id=sv1.id,
            is_default=True,
        )
    )
    await db_session.flush()

    # 第 2 個 default 同 employee — 應炸
    db_session.add(
        SkillBinding(
            tenant_id=tenant.id,
            employee_id=emp.id,
            skill_version_id=sv2.id,
            is_default=True,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_skill_binding_routing_rule_jsonb_query(db_session: AsyncSession) -> None:
    """JSONB routing_rule 可寫入結構化 rule 並查回."""
    tenant = await _make_tenant(db_session, "sb-rr-jsonb")
    skill = await _make_skill(db_session, tenant)
    sv = SkillVersion(
        skill_id=skill.id, tenant_id=tenant.id, version="1.0.0", prompt_template_ref="x"
    )
    db_session.add(sv)
    emp = Employee(
        tenant_id=tenant.id,
        name="AI",
        role="customer_service",
        status="draft",
        version="1.0.0",
    )
    db_session.add(emp)
    await db_session.flush()

    rule = {
        "type": "keyword",
        "params": {"keywords": ["請假", "leave"]},
        "priority": 10,
    }
    binding = SkillBinding(
        tenant_id=tenant.id,
        employee_id=emp.id,
        skill_version_id=sv.id,
        routing_rule=rule,
    )
    db_session.add(binding)
    await db_session.flush()
    await db_session.refresh(binding)

    assert binding.routing_rule == rule
    assert binding.routing_rule["type"] == "keyword"
    assert "請假" in binding.routing_rule["params"]["keywords"]


# ── RLS ─────────────────────────────────────────────


async def test_mc005_rls_policies_exist(db_session: AsyncSession) -> None:
    result = await db_session.execute(
        text(
            "SELECT tablename, policyname FROM pg_policies "
            "WHERE schemaname='public' "
            "AND tablename IN ('skill', 'skill_version', 'skill_binding')"
        )
    )
    policies = {(row[0], row[1]) for row in result.all()}
    assert ("skill", "skill_tenant_isolation") in policies
    assert ("skill_version", "skill_version_tenant_isolation") in policies
    assert ("skill_binding", "skill_binding_tenant_isolation") in policies
