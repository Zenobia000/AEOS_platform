"""EmployeeRuntime 行為測試 — 用 fake LLM + spy hook，不接 DB."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.agent.context import AgentContext, ToolDecision
from app.agent.hook import AgentHook
from app.agent.runtime import EmployeeRuntime
from app.llm.client import (
    LLMClient,
    LLMMessage,
    LLMResponse,
    LLMToolUse,
    LLMUsage,
)


class _FakeLLM(LLMClient):
    def __init__(self, response: LLMResponse) -> None:
        self.response = response
        self.last_kwargs: dict[str, Any] = {}

    async def complete(self, **kwargs: Any) -> LLMResponse:
        self.last_kwargs = kwargs
        return self.response


def _ctx() -> AgentContext:
    return AgentContext(
        tenant_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        employee_version="1.0.0",
        skill_version_id=uuid.uuid4(),
    )


def _resp(text: str = "ok", tool_uses: list[LLMToolUse] | None = None) -> LLMResponse:
    return LLMResponse(
        text=text,
        tool_uses=tool_uses or [],
        usage=LLMUsage(input_tokens=20, output_tokens=10),
    )


# ── 基本流程 ─────────────────────────────────────────


async def test_runtime_text_only() -> None:
    """無 tool use 時 — LLM call 後直接返回，無 tool record."""
    llm = _FakeLLM(_resp("您好"))
    runtime = EmployeeRuntime(llm=llm)

    result = await runtime.run_turn(
        ctx=_ctx(),
        messages=[LLMMessage(role="user", content="hi")],
        system="你是 AI 客服",
    )

    assert result.response.text == "您好"
    assert result.tool_calls == ()
    assert llm.last_kwargs["system"] == "你是 AI 客服"


async def test_runtime_passes_through_kwargs() -> None:
    llm = _FakeLLM(_resp())
    runtime = EmployeeRuntime(llm=llm)

    await runtime.run_turn(
        ctx=_ctx(),
        messages=[LLMMessage(role="user", content="x")],
        max_tokens=500,
        temperature=0.7,
        model="claude-haiku-4-5",
    )

    assert llm.last_kwargs["max_tokens"] == 500
    assert llm.last_kwargs["temperature"] == 0.7
    assert llm.last_kwargs["model"] == "claude-haiku-4-5"


# ── Hook 攔截順序 ───────────────────────────────────


async def test_hooks_called_around_llm() -> None:
    llm = _FakeLLM(_resp())
    spy = AgentHook()
    spy.before_llm_call = AsyncMock()  # type: ignore[method-assign]
    spy.after_llm_call = AsyncMock()  # type: ignore[method-assign]

    runtime = EmployeeRuntime(llm=llm, hook=spy)
    await runtime.run_turn(
        ctx=_ctx(),
        messages=[LLMMessage(role="user", content="x")],
    )

    spy.before_llm_call.assert_awaited_once()
    spy.after_llm_call.assert_awaited_once()


# ── Tool calls ──────────────────────────────────────


async def test_tool_use_with_executor() -> None:
    """LLM 回 tool_use → policy allow → executor 跑 → record output."""
    tu = LLMToolUse(tool_use_id="t1", name="search", input={"q": "退貨"})
    llm = _FakeLLM(_resp(tool_uses=[tu]))

    async def fake_exec(name: str, args: dict[str, Any]) -> dict[str, Any]:
        return {"results": [{"id": "kc-1"}], "for": name, "q": args["q"]}

    runtime = EmployeeRuntime(llm=llm, tool_executor=fake_exec)
    result = await runtime.run_turn(
        ctx=_ctx(),
        messages=[LLMMessage(role="user", content="退貨怎麼辦")],
    )

    assert len(result.tool_calls) == 1
    rec = result.tool_calls[0]
    assert rec.tool_name == "search"
    assert rec.decision.is_allowed is True
    assert rec.output == {
        "results": [{"id": "kc-1"}],
        "for": "search",
        "q": "退貨",
    }
    assert rec.error_message is None


async def test_tool_use_blocked_by_policy() -> None:
    """policy hook block → executor 不該被呼叫 → record 帶 error_message."""
    tu = LLMToolUse(tool_use_id="t1", name="restricted_op", input={})
    llm = _FakeLLM(_resp(tool_uses=[tu]))

    class _BlockHook(AgentHook):
        async def before_tool_call(
            self,
            ctx: AgentContext,
            tool_name: str,
            tool_input: dict[str, Any],
        ) -> ToolDecision:
            return ToolDecision.block(reason="restricted by policy", rule_name="p1")

    executor = AsyncMock()
    runtime = EmployeeRuntime(
        llm=llm,
        hook=_BlockHook(),
        tool_executor=executor,
    )

    result = await runtime.run_turn(
        ctx=_ctx(),
        messages=[LLMMessage(role="user", content="x")],
    )

    assert len(result.tool_calls) == 1
    rec = result.tool_calls[0]
    assert rec.decision.is_allowed is False
    assert rec.decision.rule_name == "p1"
    assert rec.output is None
    assert rec.error_message == "restricted by policy"
    executor.assert_not_awaited()


async def test_tool_use_executor_raises() -> None:
    """Executor raise → record output=None + error_message；不冒泡到 caller."""
    tu = LLMToolUse(tool_use_id="t1", name="search", input={})
    llm = _FakeLLM(_resp(tool_uses=[tu]))

    async def boom(name: str, args: dict[str, Any]) -> Any:
        raise ValueError("tool API down")

    runtime = EmployeeRuntime(llm=llm, tool_executor=boom)
    result = await runtime.run_turn(
        ctx=_ctx(),
        messages=[LLMMessage(role="user", content="x")],
    )

    rec = result.tool_calls[0]
    assert rec.output is None
    assert rec.error_message == "tool API down"


async def test_tool_use_no_executor() -> None:
    """無 executor → record decision.is_allowed=True + output=None（placeholder）."""
    tu = LLMToolUse(tool_use_id="t1", name="search", input={})
    llm = _FakeLLM(_resp(tool_uses=[tu]))

    runtime = EmployeeRuntime(llm=llm)  # no executor
    result = await runtime.run_turn(
        ctx=_ctx(),
        messages=[LLMMessage(role="user", content="x")],
    )

    rec = result.tool_calls[0]
    assert rec.decision.is_allowed is True
    assert rec.output is None
    assert rec.error_message is None


async def test_multiple_tool_uses_each_recorded() -> None:
    tus = [
        LLMToolUse(tool_use_id="t1", name="search", input={"q": "a"}),
        LLMToolUse(tool_use_id="t2", name="lookup", input={"id": "1"}),
    ]
    llm = _FakeLLM(_resp(tool_uses=tus))

    async def fake_exec(name: str, args: dict[str, Any]) -> str:
        return f"{name}:{args}"

    runtime = EmployeeRuntime(llm=llm, tool_executor=fake_exec)
    result = await runtime.run_turn(
        ctx=_ctx(),
        messages=[LLMMessage(role="user", content="x")],
    )

    assert len(result.tool_calls) == 2
    assert result.tool_calls[0].tool_name == "search"
    assert result.tool_calls[1].tool_name == "lookup"


# ── Hook can abort via raise ────────────────────────


async def test_hook_can_abort_before_llm() -> None:
    """before_llm_call raise → LLM 不被呼叫."""

    class _AbortHook(AgentHook):
        async def before_llm_call(self, ctx: AgentContext) -> None:
            raise PermissionError("quota exceeded")

    llm = _FakeLLM(_resp())
    runtime = EmployeeRuntime(llm=llm, hook=_AbortHook())

    with pytest.raises(PermissionError, match="quota exceeded"):
        await runtime.run_turn(
            ctx=_ctx(),
            messages=[LLMMessage(role="user", content="x")],
        )
    assert llm.last_kwargs == {}  # LLM 不該被呼叫
