"""QuotaHook 行為測試（unit，不接 DB）."""

from __future__ import annotations

import uuid

import pytest

from app.agent.context import AgentContext
from app.agent.hooks.quota import QuotaError, QuotaHook
from app.llm.client import LLMResponse, LLMUsage


def _ctx(tenant_id: uuid.UUID | None = None) -> AgentContext:
    return AgentContext(
        tenant_id=tenant_id or uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        employee_version="1.0.0",
        skill_version_id=None,
    )


def _resp(in_tok: int, out_tok: int) -> LLMResponse:
    return LLMResponse(usage=LLMUsage(input_tokens=in_tok, output_tokens=out_tok))


async def test_usage_accumulates() -> None:
    hook = QuotaHook(monthly_cap=1_000_000)
    ctx = _ctx()

    await hook.after_llm_call(ctx, _resp(100, 50))
    await hook.after_llm_call(ctx, _resp(200, 80))

    assert hook.usage(ctx.tenant_id) == 100 + 50 + 200 + 80


async def test_per_tenant_isolation() -> None:
    hook = QuotaHook()
    a = _ctx()
    b = _ctx()

    await hook.after_llm_call(a, _resp(100, 50))
    await hook.after_llm_call(b, _resp(300, 100))

    assert hook.usage(a.tenant_id) == 150
    assert hook.usage(b.tenant_id) == 400


async def test_before_llm_raises_when_over_cap() -> None:
    hook = QuotaHook(monthly_cap=100)
    ctx = _ctx()

    # 累積到剛好滿（不超）
    await hook.after_llm_call(ctx, _resp(60, 40))
    assert hook.usage(ctx.tenant_id) == 100

    # 下一次 before_llm 應 raise
    with pytest.raises(QuotaError) as exc:
        await hook.before_llm_call(ctx)
    assert exc.value.tenant_id == ctx.tenant_id
    assert exc.value.used == 100
    assert exc.value.cap == 100


async def test_before_llm_does_not_raise_under_cap() -> None:
    hook = QuotaHook(monthly_cap=10_000)
    ctx = _ctx()
    await hook.after_llm_call(ctx, _resp(100, 50))

    # 未超 cap → 不 raise
    await hook.before_llm_call(ctx)


async def test_reset_single_tenant() -> None:
    hook = QuotaHook()
    a = _ctx()
    b = _ctx()
    await hook.after_llm_call(a, _resp(100, 50))
    await hook.after_llm_call(b, _resp(200, 100))

    hook.reset(a.tenant_id)
    assert hook.usage(a.tenant_id) == 0
    assert hook.usage(b.tenant_id) == 300


async def test_reset_all() -> None:
    hook = QuotaHook()
    await hook.after_llm_call(_ctx(), _resp(10, 5))
    await hook.after_llm_call(_ctx(), _resp(20, 10))

    hook.reset()
    # 隨機選個 tenant 確認都歸零
    assert hook.usage(uuid.uuid4()) == 0
