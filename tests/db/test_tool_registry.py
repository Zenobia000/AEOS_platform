"""MC-006 Tool Registry 測試 — tool / tool_invocation / tool_policy."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.tenant import Tenant
from app.db.models.tool import Tool
from app.db.models.tool_invocation import ToolInvocation
from app.db.models.tool_policy import ToolPolicy


async def _make_tenant(session: AsyncSession, slug: str) -> Tenant:
    t = Tenant(name=f"T-{slug}", slug=slug)
    session.add(t)
    await session.flush()
    return t


def _http_tool(tenant: Tenant | None = None, slug: str = "search") -> Tool:
    return Tool(
        tenant_id=tenant.id if tenant else None,
        slug=slug,
        name="Search Knowledge",
        description="搜尋 KB 中與問題最相關的 KC",
        tool_type="http_api",
        endpoint="https://api.internal/search",
        auth_method="api_key",
        auth_config={"key_ref": "secret://tools/search/key"},
        input_schema={"type": "object", "properties": {"q": {"type": "string"}}},
        output_schema={"type": "array"},
        risk_tier="safe",
    )


# ── Tool ────────────────────────────────────────────


async def test_tool_create_with_defaults(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "tool-create")
    t = _http_tool(tenant)
    db_session.add(t)
    await db_session.flush()

    assert t.id is not None
    assert t.enabled is True
    assert t.rate_limit_rpm == 60
    assert t.timeout_ms == 5000
    assert t.retry_policy == {"max_retries": 2, "backoff_ms": 500}


async def test_tool_type_check(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "tool-bad-type")
    t = _http_tool(tenant, slug="bad")
    t.tool_type = "weird"
    db_session.add(t)
    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()
    assert "tool_type_check" in str(exc.value).lower()


async def test_tool_risk_tier_check(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "tool-bad-risk")
    t = _http_tool(tenant, slug="bad")
    t.risk_tier = "extreme"  # 不在 safe/caution/restricted
    db_session.add(t)
    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()
    assert "risk_tier_check" in str(exc.value).lower()


async def test_tool_auth_method_optional(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "tool-noauth")
    t = _http_tool(tenant, slug="noauth")
    t.auth_method = None
    t.auth_config = None
    db_session.add(t)
    await db_session.flush()
    assert t.auth_method is None


async def test_tool_unique_slug_per_tenant(db_session: AsyncSession) -> None:
    """同 tenant 不能有兩個相同 slug 的 tool（partial unique index）."""
    tenant = await _make_tenant(db_session, "tool-uniq")
    db_session.add(_http_tool(tenant, slug="search_knowledge"))
    await db_session.flush()
    db_session.add(_http_tool(tenant, slug="search_knowledge"))
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_tool_system_builtin_null_tenant(db_session: AsyncSession) -> None:
    """tenant_id NULL = 系統內建 tool；可建立."""
    t = _http_tool(tenant=None, slug="sys-builtin")
    db_session.add(t)
    await db_session.flush()
    assert t.id is not None
    assert t.tenant_id is None


# ── ToolInvocation ─────────────────────────────────


async def test_tool_invocation_success(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "inv-ok")
    t = _http_tool(tenant, slug="search")
    db_session.add(t)
    await db_session.flush()

    inv = ToolInvocation(
        tenant_id=tenant.id,
        tool_id=t.id,
        input={"q": "退貨"},
        output=[{"kc_id": "abc"}],
        status="success",
        latency_ms=123,
        cost_token=80,
    )
    db_session.add(inv)
    await db_session.flush()

    assert inv.id is not None
    assert inv.status == "success"


async def test_tool_invocation_status_check(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "inv-bad")
    t = _http_tool(tenant, slug="search")
    db_session.add(t)
    await db_session.flush()

    inv = ToolInvocation(
        tenant_id=tenant.id,
        tool_id=t.id,
        input={"q": "x"},
        status="weird_status",
    )
    db_session.add(inv)
    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()
    assert "status_check" in str(exc.value).lower()


async def test_tool_invocation_rejected_by_policy(db_session: AsyncSession) -> None:
    """記錄被 policy 擋下的 tool call（無 output、有 policy_decision）."""
    tenant = await _make_tenant(db_session, "inv-policy")
    t = _http_tool(tenant, slug="search")
    db_session.add(t)
    await db_session.flush()

    inv = ToolInvocation(
        tenant_id=tenant.id,
        tool_id=t.id,
        input={"q": "查訂單 #123"},
        status="rejected_by_policy",
        policy_decision={
            "allowed": False,
            "rule": "rule-007-restricted-pii",
            "reason": "user did not consent to data sharing",
        },
    )
    db_session.add(inv)
    await db_session.flush()

    assert inv.policy_decision is not None
    assert inv.policy_decision["allowed"] is False


# ── ToolPolicy ─────────────────────────────────────


async def test_tool_policy_create_global(db_session: AsyncSession) -> None:
    """tenant_id=None → 全局 policy（適用所有 tenant）."""
    pol = ToolPolicy(
        tenant_id=None,
        name="block_restricted_in_canary",
        description="canary 期間不開放 restricted tool",
        rule_yaml="when: phase == 'canary'\nblock: tool.risk_tier == 'restricted'",
        priority=100,
    )
    db_session.add(pol)
    await db_session.flush()
    assert pol.id is not None
    assert pol.enabled is True


async def test_tool_policy_tenant_scoped(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "policy-tenant")
    pol = ToolPolicy(
        tenant_id=tenant.id,
        name="tenant_x_custom",
        rule_yaml="when: true\nallow: true",
    )
    db_session.add(pol)
    await db_session.flush()
    assert pol.tenant_id == tenant.id


# ── RLS ─────────────────────────────────────────────


async def test_mc006_rls_policies_exist(db_session: AsyncSession) -> None:
    result = await db_session.execute(
        text(
            "SELECT tablename, policyname FROM pg_policies "
            "WHERE schemaname='public' "
            "AND tablename IN ('tool', 'tool_invocation', 'tool_policy')"
        )
    )
    policies = {(row[0], row[1]) for row in result.all()}
    assert ("tool", "tool_tenant_isolation") in policies
    assert ("tool_invocation", "tool_invocation_tenant_isolation") in policies
    assert ("tool_policy", "tool_policy_tenant_isolation") in policies
