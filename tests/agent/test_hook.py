"""AgentHook + CompositeHook + ToolDecision 行為測試（unit, 不接 DB）."""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from app.agent.context import AgentContext, ToolDecision
from app.agent.hook import AgentHook, CompositeHook
from app.llm.client import LLMResponse, LLMUsage


def _make_ctx() -> AgentContext:
    return AgentContext(
        tenant_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        employee_version="1.0.0",
        skill_version_id=uuid.uuid4(),
    )


def _make_response(text: str = "ok", in_tok: int = 10, out_tok: int = 5) -> LLMResponse:
    return LLMResponse(
        text=text,
        usage=LLMUsage(input_tokens=in_tok, output_tokens=out_tok),
    )


# ── ToolDecision ────────────────────────────────────


def test_tool_decision_allow() -> None:
    d = ToolDecision.allow("ok")
    assert d.is_allowed is True
    assert d.reason == "ok"
    assert d.rule_name is None


def test_tool_decision_block() -> None:
    d = ToolDecision.block("blocked by policy", rule_name="rule-1")
    assert d.is_allowed is False
    assert d.rule_name == "rule-1"


# ── Default AgentHook（no-op）────────────────────────


async def test_default_hook_all_noop() -> None:
    h = AgentHook()
    ctx = _make_ctx()
    await h.before_llm_call(ctx)
    await h.after_llm_call(ctx, _make_response())
    decision = await h.before_tool_call(ctx, "search", {"q": "x"})
    assert decision.is_allowed is True
    await h.after_tool_call(ctx, "search", {"q": "x"}, tool_output={"x": 1})


# ── CompositeHook ──────────────────────────────────


class _RecordingHook(AgentHook):
    def __init__(self, name: str, block_tool: str | None = None) -> None:
        self.name = name
        self.block_tool = block_tool
        self.calls: list[str] = []

    async def before_llm_call(self, ctx: AgentContext) -> None:
        self.calls.append("before_llm")

    async def after_llm_call(self, ctx: AgentContext, response: LLMResponse) -> None:
        self.calls.append(f"after_llm_{response.usage.total_tokens}")

    async def before_tool_call(
        self,
        ctx: AgentContext,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> ToolDecision:
        self.calls.append(f"before_tool_{tool_name}")
        if self.block_tool and tool_name == self.block_tool:
            return ToolDecision.block(
                reason=f"{self.name} blocks {tool_name}",
                rule_name=self.name,
            )
        return ToolDecision.allow()

    async def after_tool_call(
        self,
        ctx: AgentContext,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: Any,
        error: Exception | None = None,
    ) -> None:
        self.calls.append(f"after_tool_{tool_name}_{error is not None}")


async def test_composite_runs_all_hooks_in_order() -> None:
    h1 = _RecordingHook("A")
    h2 = _RecordingHook("B")
    comp = CompositeHook([h1, h2])
    ctx = _make_ctx()

    await comp.before_llm_call(ctx)
    await comp.after_llm_call(ctx, _make_response())
    assert h1.calls == ["before_llm", "after_llm_15"]
    assert h2.calls == ["before_llm", "after_llm_15"]


async def test_composite_short_circuits_on_block() -> None:
    """第一個 hook block 後，第二個 hook 不應被呼叫."""
    h1 = _RecordingHook("A", block_tool="lookup_pii")
    h2 = _RecordingHook("B")
    comp = CompositeHook([h1, h2])
    ctx = _make_ctx()

    decision = await comp.before_tool_call(ctx, "lookup_pii", {})
    assert decision.is_allowed is False
    assert decision.rule_name == "A"
    assert "before_tool_lookup_pii" in h1.calls
    assert "before_tool_lookup_pii" not in h2.calls


async def test_composite_allow_passes_through() -> None:
    h1 = _RecordingHook("A")
    h2 = _RecordingHook("B", block_tool="restricted_tool")
    comp = CompositeHook([h1, h2])
    ctx = _make_ctx()

    decision = await comp.before_tool_call(ctx, "search_knowledge", {})
    assert decision.is_allowed is True
    # 兩個 hook 都應該收到 before_tool_call
    assert "before_tool_search_knowledge" in h1.calls
    assert "before_tool_search_knowledge" in h2.calls


async def test_composite_hooks_property_exposed() -> None:
    h1 = _RecordingHook("A")
    comp = CompositeHook([h1])
    assert comp.hooks == (h1,)


# ── Hook 子類能 raise 中止 ──────────────────────────


class _RaisingHook(AgentHook):
    async def before_llm_call(self, ctx: AgentContext) -> None:
        raise RuntimeError("boom")


async def test_hook_can_raise_to_abort() -> None:
    h = _RaisingHook()
    ctx = _make_ctx()
    with pytest.raises(RuntimeError, match="boom"):
        await h.before_llm_call(ctx)
