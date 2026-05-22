"""EmployeeRuntime — 對話一回合的入口.

依 MC-009 (Employee Runtime) + engineering-charter §2 (Frozen Runtime)
+ ADR-0012 §11.2（借鑑 nanobot agent loop 設計）：

設計選擇：
- Phase 1 = 單次 LLM call per turn（不做 multi-turn tool loop）；如果
  LLM 回 tool_use，由本 layer 執行 tool 一次後不再回送給 LLM。完整
  agent loop（多輪 tool calling）是 Phase 2 / S5 工作。
- runtime_snapshot 由 AgentContext 攜帶；本 class 不直接讀 employee row，
  以保 Frozen Runtime 原則
- Tool 執行：本 class 不執行具體 tool；ToolExecutor 由外部注入（依 MC-006
  Tool Registry 的 endpoint / function_type 分派）。Phase 1 為簡化，
  允許 ToolExecutor 為 None — 此時 tool_use 不執行只 return placeholder
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from app.agent.context import AgentContext, ToolDecision
from app.agent.hook import AgentHook
from app.llm.client import (
    LLMClient,
    LLMMessage,
    LLMResponse,
    LLMToolDefinition,
    LLMToolUse,
)

ToolExecutor = Callable[[str, dict[str, Any]], Awaitable[Any]]


@dataclass(frozen=True)
class ToolCallRecord:
    """單次 tool call 的結果記錄."""

    tool_name: str
    tool_input: dict[str, Any]
    decision: ToolDecision
    output: Any = None
    error_message: str | None = None


@dataclass(frozen=True)
class TurnResult:
    """`run_turn()` 回傳值."""

    response: LLMResponse
    tool_calls: Sequence[ToolCallRecord] = field(default_factory=list)


class EmployeeRuntime:
    """單次 turn runtime — 載入 frozen snapshot + 呼叫 LLM + 跑 hooks.

    Args:
        llm: LLMClient 實作（Phase 1: AnthropicClient）
        hook: 單一 hook 或 CompositeHook（governance layer）
        tool_executor: 可選 callable(tool_name, input) -> output；
                       Phase 1 簡化情境可為 None
    """

    def __init__(
        self,
        *,
        llm: LLMClient,
        hook: AgentHook | None = None,
        tool_executor: ToolExecutor | None = None,
    ) -> None:
        self._llm = llm
        self._hook = hook or AgentHook()
        self._tool_executor = tool_executor

    async def run_turn(
        self,
        *,
        ctx: AgentContext,
        messages: Sequence[LLMMessage],
        system: str | None = None,
        tools: Sequence[LLMToolDefinition] | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        model: str | None = None,
    ) -> TurnResult:
        """單次 turn：before_llm_call → LLM complete → after_llm_call
        → 對每個 tool_use 跑 policy → execute → after_tool_call.
        """
        # ── 1. before LLM ────────────────────────────────
        await self._hook.before_llm_call(ctx)

        # ── 2. LLM call ──────────────────────────────────
        response = await self._llm.complete(
            messages=messages,
            system=system,
            tools=tools,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
        )

        # ── 3. after LLM ─────────────────────────────────
        await self._hook.after_llm_call(ctx, response)

        # ── 4. tool calls（如有）──────────────────────────
        records: list[ToolCallRecord] = []
        for tool_use in response.tool_uses:
            record = await self._handle_tool_use(ctx, tool_use)
            records.append(record)

        return TurnResult(response=response, tool_calls=tuple(records))

    async def _handle_tool_use(
        self,
        ctx: AgentContext,
        tool_use: LLMToolUse,
    ) -> ToolCallRecord:
        decision = await self._hook.before_tool_call(ctx, tool_use.name, tool_use.input)

        if not decision.is_allowed:
            await self._hook.after_tool_call(
                ctx,
                tool_use.name,
                tool_use.input,
                tool_output=None,
                error=PermissionError(decision.reason),
            )
            return ToolCallRecord(
                tool_name=tool_use.name,
                tool_input=tool_use.input,
                decision=decision,
                output=None,
                error_message=decision.reason,
            )

        if self._tool_executor is None:
            await self._hook.after_tool_call(
                ctx,
                tool_use.name,
                tool_use.input,
                tool_output=None,
                error=None,
            )
            return ToolCallRecord(
                tool_name=tool_use.name,
                tool_input=tool_use.input,
                decision=decision,
                output=None,
            )

        try:
            output = await self._tool_executor(tool_use.name, tool_use.input)
            error: Exception | None = None
            error_message: str | None = None
        except Exception as exc:
            output = None
            error = exc
            error_message = str(exc)

        await self._hook.after_tool_call(
            ctx,
            tool_use.name,
            tool_use.input,
            tool_output=output,
            error=error,
        )

        return ToolCallRecord(
            tool_name=tool_use.name,
            tool_input=tool_use.input,
            decision=decision,
            output=output,
            error_message=error_message,
        )
