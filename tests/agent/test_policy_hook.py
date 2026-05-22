"""PolicyHook 行為測試 — 需 DB（tool + tool_policy 表）."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.context import AgentContext
from app.agent.hooks.policy import PolicyHook
from app.db.models.tenant import Tenant
from app.db.models.tool import Tool
from app.db.models.tool_policy import ToolPolicy


async def _seed_tenant(session: AsyncSession, slug: str) -> Tenant:
    t = Tenant(name=f"T-{slug}", slug=slug)
    session.add(t)
    await session.flush()
    return t


async def _seed_tool(
    session: AsyncSession,
    slug: str,
    risk_tier: str = "safe",
    enabled: bool = True,
) -> Tool:
    t = Tool(
        tenant_id=None,
        slug=slug,
        name=slug,
        description=f"tool {slug}",
        tool_type="internal",
        input_schema={"type": "object"},
        risk_tier=risk_tier,
        enabled=enabled,
    )
    session.add(t)
    await session.flush()
    return t


def _ctx(session: AsyncSession, tenant_id: uuid.UUID) -> AgentContext:
    return AgentContext(
        tenant_id=tenant_id,
        conversation_id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        employee_version="1.0.0",
        skill_version_id=uuid.uuid4(),
        session=session,
    )


# ── 基本允許 ────────────────────────────────────────


async def test_policy_allows_when_no_policies(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, "p-allow")
    await _seed_tool(db_session, "search_knowledge")

    hook = PolicyHook()
    decision = await hook.before_tool_call(
        _ctx(db_session, tenant.id),
        "search_knowledge",
        {"q": "x"},
    )
    assert decision.is_allowed is True


# ── 阻擋未註冊 tool ─────────────────────────────────


async def test_policy_blocks_unknown_tool(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, "p-unknown")
    hook = PolicyHook()
    decision = await hook.before_tool_call(
        _ctx(db_session, tenant.id),
        "no_such_tool",
        {},
    )
    assert decision.is_allowed is False
    assert decision.rule_name == "tool_not_registered"


async def test_policy_blocks_disabled_tool(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, "p-disabled")
    await _seed_tool(db_session, "old_tool", enabled=False)

    hook = PolicyHook()
    decision = await hook.before_tool_call(
        _ctx(db_session, tenant.id),
        "old_tool",
        {},
    )
    assert decision.is_allowed is False
    assert decision.rule_name == "tool_disabled"


# ── YAML rule：block_risk_tier ──────────────────────


async def test_policy_block_by_risk_tier(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, "p-tier")
    await _seed_tool(db_session, "lookup_pii", risk_tier="restricted")
    db_session.add(
        ToolPolicy(
            tenant_id=None,
            name="block_restricted",
            rule_yaml="block_risk_tier: restricted",
            priority=100,
        )
    )
    await db_session.flush()

    hook = PolicyHook()
    decision = await hook.before_tool_call(
        _ctx(db_session, tenant.id),
        "lookup_pii",
        {},
    )
    assert decision.is_allowed is False
    assert decision.rule_name == "block_restricted"
    assert "restricted" in decision.reason


# ── YAML rule：block_tool ──────────────────────────


async def test_policy_block_by_slug(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, "p-slug")
    await _seed_tool(db_session, "dangerous_op", risk_tier="safe")
    db_session.add(
        ToolPolicy(
            tenant_id=None,
            name="block_dangerous_op",
            rule_yaml="block_tool: dangerous_op",
            priority=50,
        )
    )
    await db_session.flush()

    hook = PolicyHook()
    decision = await hook.before_tool_call(
        _ctx(db_session, tenant.id),
        "dangerous_op",
        {},
    )
    assert decision.is_allowed is False
    assert decision.rule_name == "block_dangerous_op"


# ── Priority ordering（高 priority 先評估） ────────


async def test_policy_priority_high_first(db_session: AsyncSession) -> None:
    """兩條 policy 都會阻擋；確認 high-priority 是 reported rule."""
    tenant = await _seed_tenant(db_session, "p-pri")
    await _seed_tool(db_session, "x", risk_tier="caution")
    db_session.add(
        ToolPolicy(
            tenant_id=None,
            name="low_rule",
            rule_yaml="block_risk_tier: caution",
            priority=10,
        )
    )
    db_session.add(
        ToolPolicy(
            tenant_id=None,
            name="high_rule",
            rule_yaml="block_risk_tier: caution",
            priority=100,
        )
    )
    await db_session.flush()

    hook = PolicyHook()
    decision = await hook.before_tool_call(
        _ctx(db_session, tenant.id),
        "x",
        {},
    )
    assert decision.is_allowed is False
    assert decision.rule_name == "high_rule"


# ── Disabled policy 不評估 ──────────────────────────


async def test_disabled_policy_ignored(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, "p-disabled")
    await _seed_tool(db_session, "restricted_op", risk_tier="restricted")
    db_session.add(
        ToolPolicy(
            tenant_id=None,
            name="should_be_ignored",
            rule_yaml="block_risk_tier: restricted",
            priority=100,
            enabled=False,
        )
    )
    await db_session.flush()

    hook = PolicyHook()
    decision = await hook.before_tool_call(
        _ctx(db_session, tenant.id),
        "restricted_op",
        {},
    )
    # disabled 不參與評估 → 應 allow
    assert decision.is_allowed is True


# ── Malformed YAML rule 安全處理 ────────────────────


async def test_malformed_yaml_does_not_crash(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, "p-yaml")
    await _seed_tool(db_session, "ok_tool")
    db_session.add(
        ToolPolicy(
            tenant_id=None,
            name="broken_rule",
            rule_yaml="[: this is not valid yaml: :",
            priority=10,
        )
    )
    await db_session.flush()

    hook = PolicyHook()
    decision = await hook.before_tool_call(
        _ctx(db_session, tenant.id),
        "ok_tool",
        {},
    )
    # malformed rule 不應 crash，視為不適用 → allow
    assert decision.is_allowed is True


# ── No session → allow（pass-through） ──────────────


async def test_no_session_pass_through() -> None:
    hook = PolicyHook()
    ctx = AgentContext(
        tenant_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        employee_version="1.0.0",
        skill_version_id=None,
        session=None,
    )
    decision = await hook.before_tool_call(ctx, "anything", {})
    assert decision.is_allowed is True
