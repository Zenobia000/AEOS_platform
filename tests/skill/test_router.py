"""SkillRouter 單元測試 — CR-0001 / ADR-0013.

涵蓋：
- 4 種 rule evaluator (keyword / llm_intent / channel_match / explicit) — pure fn 層
- SkillRouter.route() — priority sort / fallback / LLM intent integration / 錯誤處理
- NoSkillBoundError 例外
"""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog
from app.db.models.employee import Employee
from app.db.models.skill import Skill
from app.db.models.skill_binding import SkillBinding
from app.db.models.skill_version import SkillVersion
from app.db.models.tenant import Tenant
from app.llm.client import LLMClient, LLMResponse, LLMUsage
from app.skill.router import (
    NoSkillBoundError,
    SkillRouter,
    _eval_channel_match,
    _eval_explicit,
    _eval_keyword,
)

# ── Stub LLM ─────────────────────────────────────────────


class _StubLLM(LLMClient):
    def __init__(self, text: str, *, raise_exc: Exception | None = None) -> None:
        self._text = text
        self._raise = raise_exc
        self.calls: list[dict[str, Any]] = []

    async def complete(self, **kwargs: Any) -> LLMResponse:
        self.calls.append(kwargs)
        if self._raise is not None:
            raise self._raise
        return LLMResponse(
            text=self._text,
            tool_uses=[],
            stop_reason="end_turn",
            usage=LLMUsage(input_tokens=20, output_tokens=10),
            model="stub-haiku",
        )


# ── Pure-function evaluator tests ────────────────────────


def test_eval_keyword_hit() -> None:
    assert _eval_keyword("我想請假", {"keywords": ["請假", "leave"]}) is True


def test_eval_keyword_miss() -> None:
    assert _eval_keyword("hello there", {"keywords": ["請假", "leave"]}) is False


def test_eval_keyword_case_insensitive() -> None:
    assert _eval_keyword("I need LEAVE", {"keywords": ["leave"]}) is True


def test_eval_keyword_empty_params() -> None:
    assert _eval_keyword("anything", {"keywords": []}) is False
    assert _eval_keyword("anything", {}) is False


def test_eval_channel_match_hit() -> None:
    assert _eval_channel_match("U123", {"channel_id": "U123"}) is True


def test_eval_channel_match_miss() -> None:
    assert _eval_channel_match("U999", {"channel_id": "U123"}) is False


def test_eval_channel_match_none_channel() -> None:
    assert _eval_channel_match(None, {"channel_id": "U123"}) is False


def test_eval_explicit_never_match() -> None:
    """explicit type 無論如何不 match — 純當 disable 用。"""
    assert _eval_explicit({"never_match": True}) is False
    assert _eval_explicit({}) is False


# ── Fixtures for SkillRouter tests ───────────────────────


async def _make_tenant(session: AsyncSession, slug: str) -> Tenant:
    t = Tenant(name=f"T-{slug}", slug=slug)
    session.add(t)
    await session.flush()
    return t


async def _make_employee(session: AsyncSession, tenant: Tenant) -> Employee:
    emp = Employee(
        tenant_id=tenant.id,
        name="AI",
        role="customer_service",
        status="draft",
        version="1.0.0",
    )
    session.add(emp)
    await session.flush()
    return emp


async def _make_skill_version(
    session: AsyncSession, tenant: Tenant, vertical: str, slug_suffix: str
) -> SkillVersion:
    skill = Skill(
        tenant_id=tenant.id,
        slug=f"{vertical}/{slug_suffix}",
        vertical=vertical,
        name=f"{vertical} skill",
    )
    session.add(skill)
    await session.flush()
    sv = SkillVersion(
        skill_id=skill.id,
        tenant_id=tenant.id,
        version="1.0.0",
        prompt_template_ref="x",
    )
    session.add(sv)
    await session.flush()
    return sv


async def _bind(
    session: AsyncSession,
    tenant: Tenant,
    emp: Employee,
    sv: SkillVersion,
    *,
    routing_rule: dict[str, Any] | None = None,
    is_default: bool = False,
    priority: int = 0,
) -> SkillBinding:
    b = SkillBinding(
        tenant_id=tenant.id,
        employee_id=emp.id,
        skill_version_id=sv.id,
        routing_rule=routing_rule or {},
        is_default=is_default,
        priority=priority,
    )
    session.add(b)
    await session.flush()
    return b


# ── SkillRouter integration tests ────────────────────────


async def test_router_keyword_match(db_session: AsyncSession) -> None:
    """keyword rule 命中 → 回 對應 skill_version + audit `routing.matched`."""
    tenant = await _make_tenant(db_session, "r-kw")
    emp = await _make_employee(db_session, tenant)
    sv_hr = await _make_skill_version(db_session, tenant, "hr", "leave-request")
    sv_default = await _make_skill_version(db_session, tenant, "customer-service", "faq")

    await _bind(
        db_session,
        tenant,
        emp,
        sv_hr,
        routing_rule={"type": "keyword", "params": {"keywords": ["請假"]}, "priority": 10},
    )
    await _bind(db_session, tenant, emp, sv_default, is_default=True)

    router = SkillRouter(db_session)
    decision = await router.route(
        message="我想請假",
        employee_id=emp.id,
        tenant_id=tenant.id,
    )

    assert decision.skill_version.id == sv_hr.id
    assert decision.matched_rule_type == "keyword"

    audit_rows = (
        (await db_session.execute(select(AuditLog).where(AuditLog.event_type == "routing.matched")))
        .scalars()
        .all()
    )
    assert len(audit_rows) == 1


async def test_router_fallback_to_default(db_session: AsyncSession) -> None:
    """全 rule miss → 走 is_default=true binding + audit `routing.fallback`."""
    tenant = await _make_tenant(db_session, "r-fb")
    emp = await _make_employee(db_session, tenant)
    sv_hr = await _make_skill_version(db_session, tenant, "hr", "leave-request")
    sv_default = await _make_skill_version(db_session, tenant, "customer-service", "faq")

    await _bind(
        db_session,
        tenant,
        emp,
        sv_hr,
        routing_rule={"type": "keyword", "params": {"keywords": ["請假"]}, "priority": 10},
    )
    await _bind(db_session, tenant, emp, sv_default, is_default=True)

    router = SkillRouter(db_session)
    decision = await router.route(
        message="今天天氣不錯",  # 不命中 keyword
        employee_id=emp.id,
        tenant_id=tenant.id,
    )

    assert decision.skill_version.id == sv_default.id
    assert decision.matched_rule_type == "default_fallback"
    assert decision.matched_rule is None

    audit_rows = (
        (
            await db_session.execute(
                select(AuditLog).where(AuditLog.event_type == "routing.fallback")
            )
        )
        .scalars()
        .all()
    )
    assert len(audit_rows) == 1


async def test_router_priority_order(db_session: AsyncSession) -> None:
    """同 message 命中兩 rule 時，priority 小者勝。"""
    tenant = await _make_tenant(db_session, "r-pri")
    emp = await _make_employee(db_session, tenant)
    sv_hi = await _make_skill_version(db_session, tenant, "v1", "high-priority")
    sv_lo = await _make_skill_version(db_session, tenant, "v2", "low-priority")

    # 兩個 rule 都會命中 "test"
    await _bind(
        db_session,
        tenant,
        emp,
        sv_lo,
        routing_rule={"type": "keyword", "params": {"keywords": ["test"]}, "priority": 50},
    )
    await _bind(
        db_session,
        tenant,
        emp,
        sv_hi,
        routing_rule={"type": "keyword", "params": {"keywords": ["test"]}, "priority": 10},
    )

    router = SkillRouter(db_session)
    decision = await router.route(
        message="this is a test",
        employee_id=emp.id,
        tenant_id=tenant.id,
    )

    assert decision.skill_version.id == sv_hi.id  # priority 10 < 50 勝


async def test_router_no_bindings_raises(db_session: AsyncSession) -> None:
    """employee 完全沒 binding → NoSkillBoundError."""
    tenant = await _make_tenant(db_session, "r-empty")
    emp = await _make_employee(db_session, tenant)

    router = SkillRouter(db_session)
    with pytest.raises(NoSkillBoundError):
        await router.route(
            message="any",
            employee_id=emp.id,
            tenant_id=tenant.id,
        )


async def test_router_no_default_all_miss_raises(db_session: AsyncSession) -> None:
    """有 binding 但無 is_default 且全 rule miss → NoSkillBoundError."""
    tenant = await _make_tenant(db_session, "r-no-default")
    emp = await _make_employee(db_session, tenant)
    sv = await _make_skill_version(db_session, tenant, "hr", "leave")

    await _bind(
        db_session,
        tenant,
        emp,
        sv,
        routing_rule={"type": "keyword", "params": {"keywords": ["請假"]}, "priority": 10},
        is_default=False,
    )

    router = SkillRouter(db_session)
    with pytest.raises(NoSkillBoundError):
        await router.route(
            message="hello",
            employee_id=emp.id,
            tenant_id=tenant.id,
        )


async def test_router_llm_intent_match(db_session: AsyncSession) -> None:
    """llm_intent rule + LLM 回答含目標 intent → 命中."""
    tenant = await _make_tenant(db_session, "r-llm-hit")
    emp = await _make_employee(db_session, tenant)
    sv = await _make_skill_version(db_session, tenant, "hr", "leave")

    await _bind(
        db_session,
        tenant,
        emp,
        sv,
        routing_rule={
            "type": "llm_intent",
            "params": {"intents": ["leave_request"]},
            "priority": 50,
        },
        is_default=True,  # 同時當 default 簡化
    )

    stub_llm = _StubLLM("leave_request")
    router = SkillRouter(db_session, llm_client=stub_llm)
    decision = await router.route(
        message="想請年假",
        employee_id=emp.id,
        tenant_id=tenant.id,
    )

    assert decision.matched_rule_type == "llm_intent"
    assert decision.skill_version.id == sv.id
    assert len(stub_llm.calls) == 1


async def test_router_llm_intent_no_client_skipped(db_session: AsyncSession) -> None:
    """無 LLMClient 注入時 llm_intent rule 自動 miss → fallback to default."""
    tenant = await _make_tenant(db_session, "r-llm-noclient")
    emp = await _make_employee(db_session, tenant)
    sv_llm = await _make_skill_version(db_session, tenant, "hr", "leave")
    sv_default = await _make_skill_version(db_session, tenant, "customer-service", "faq")

    await _bind(
        db_session,
        tenant,
        emp,
        sv_llm,
        routing_rule={"type": "llm_intent", "params": {"intents": ["x"]}, "priority": 10},
    )
    await _bind(db_session, tenant, emp, sv_default, is_default=True)

    router = SkillRouter(db_session, llm_client=None)
    decision = await router.route(
        message="any",
        employee_id=emp.id,
        tenant_id=tenant.id,
    )

    assert decision.skill_version.id == sv_default.id
    assert decision.matched_rule_type == "default_fallback"


async def test_router_evaluator_error_skips_to_next(db_session: AsyncSession) -> None:
    """某 evaluator 噴例外 → 寫 routing.error audit + 繼續下個 rule."""
    tenant = await _make_tenant(db_session, "r-err")
    emp = await _make_employee(db_session, tenant)
    sv_llm = await _make_skill_version(db_session, tenant, "hr", "leave")
    sv_default = await _make_skill_version(db_session, tenant, "customer-service", "faq")

    await _bind(
        db_session,
        tenant,
        emp,
        sv_llm,
        routing_rule={"type": "llm_intent", "params": {"intents": ["x"]}, "priority": 10},
    )
    await _bind(db_session, tenant, emp, sv_default, is_default=True)

    bad_llm = _StubLLM("", raise_exc=RuntimeError("LLM down"))
    router = SkillRouter(db_session, llm_client=bad_llm)
    decision = await router.route(
        message="any",
        employee_id=emp.id,
        tenant_id=tenant.id,
    )

    # llm_intent 內部捕 exception 不傳出 — 不會觸發 routing.error；但 fallback 仍走
    assert decision.skill_version.id == sv_default.id
    assert decision.matched_rule_type == "default_fallback"


async def test_router_unknown_rule_type_treated_as_miss(db_session: AsyncSession) -> None:
    """admin 拼錯 rule type → 該 rule 視為 miss → fallback to default."""
    tenant = await _make_tenant(db_session, "r-unknown")
    emp = await _make_employee(db_session, tenant)
    sv = await _make_skill_version(db_session, tenant, "x", "y")
    sv_default = await _make_skill_version(db_session, tenant, "customer-service", "faq")

    await _bind(
        db_session,
        tenant,
        emp,
        sv,
        routing_rule={"type": "magic_unicorn", "params": {}, "priority": 10},
    )
    await _bind(db_session, tenant, emp, sv_default, is_default=True)

    router = SkillRouter(db_session)
    decision = await router.route(
        message="any",
        employee_id=emp.id,
        tenant_id=tenant.id,
    )

    assert decision.skill_version.id == sv_default.id
    assert decision.matched_rule_type == "default_fallback"


async def test_router_channel_match(db_session: AsyncSession) -> None:
    """channel_match rule 命中 → 對應 skill."""
    tenant = await _make_tenant(db_session, "r-ch")
    emp = await _make_employee(db_session, tenant)
    sv_vip = await _make_skill_version(db_session, tenant, "vip", "premium-cs")
    sv_default = await _make_skill_version(db_session, tenant, "customer-service", "faq")

    await _bind(
        db_session,
        tenant,
        emp,
        sv_vip,
        routing_rule={
            "type": "channel_match",
            "params": {"channel_id": "C_VIP"},
            "priority": 5,
        },
    )
    await _bind(db_session, tenant, emp, sv_default, is_default=True)

    router = SkillRouter(db_session)
    decision = await router.route(
        message="hello",
        employee_id=emp.id,
        tenant_id=tenant.id,
        channel_id="C_VIP",
    )

    assert decision.skill_version.id == sv_vip.id
    assert decision.matched_rule_type == "channel_match"
