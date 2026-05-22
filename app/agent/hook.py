"""AgentHook — Governance Layer 攔截點.

依 ADR-0012 §11.2 借鑑 nanobot/agent/hook.py 設計 + engineering-charter §1
(Governance-first)：

- before_llm_call / after_llm_call: LLM 呼叫前後攔截（quota check / usage 記錄）
- before_tool_call: 回 ToolDecision；block 即不執行（policy engine 落地點）
- after_tool_call: tool 結果記錄（audit / metrics）

設計差異於 nanobot：
- 不支援 streaming hook（Phase 1 simplicity；S4 加）
- before_tool_call 強制回 ToolDecision（不是 mutate context）— 不可變 context 原則
- CompositeHook 串接時 block 立即短路，不繼續評估後續 hook
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.agent.context import AgentContext, ToolDecision
from app.llm.client import LLMResponse


class AgentHook:
    """Hook 基類；子類覆寫想 intercept 的方法。預設都 no-op."""

    async def before_llm_call(self, ctx: AgentContext) -> None:
        """LLM call 前；可 raise 中止（如 QuotaHook 超額時）."""
        return None

    async def after_llm_call(
        self,
        ctx: AgentContext,
        response: LLMResponse,
    ) -> None:
        """LLM call 後；用於 audit / quota usage 記錄."""
        return None

    async def before_tool_call(
        self,
        ctx: AgentContext,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> ToolDecision:
        """Tool call 前；回 ToolDecision.block 可阻擋執行."""
        return ToolDecision.allow()

    async def after_tool_call(
        self,
        ctx: AgentContext,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: Any,
        error: Exception | None = None,
    ) -> None:
        """Tool call 後；用於 audit / metrics."""
        return None


class CompositeHook(AgentHook):
    """串接多個 hook；before_tool_call block 短路."""

    def __init__(self, hooks: Sequence[AgentHook]) -> None:
        self._hooks: tuple[AgentHook, ...] = tuple(hooks)

    @property
    def hooks(self) -> tuple[AgentHook, ...]:
        return self._hooks

    async def before_llm_call(self, ctx: AgentContext) -> None:
        for h in self._hooks:
            await h.before_llm_call(ctx)

    async def after_llm_call(
        self,
        ctx: AgentContext,
        response: LLMResponse,
    ) -> None:
        for h in self._hooks:
            await h.after_llm_call(ctx, response)

    async def before_tool_call(
        self,
        ctx: AgentContext,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> ToolDecision:
        for h in self._hooks:
            decision = await h.before_tool_call(ctx, tool_name, tool_input)
            if not decision.is_allowed:
                return decision  # short-circuit on first block
        return ToolDecision.allow()

    async def after_tool_call(
        self,
        ctx: AgentContext,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: Any,
        error: Exception | None = None,
    ) -> None:
        for h in self._hooks:
            await h.after_tool_call(ctx, tool_name, tool_input, tool_output, error)
