"""AuditHook — 把 agent 所有對外行為寫進 MC-001 audit_log.

依 engineering-charter §1 Governance-first：
> 所有 AI 對外行為先 audit log + policy check；無此路徑禁上線

事件型別命名遵循 db-schema.md §1 line 30：`module.action` 點分小寫格式.
"""

from __future__ import annotations

from typing import Any

from app.agent.context import AgentContext
from app.agent.hook import AgentHook
from app.llm.client import LLMResponse
from app.services import audit


class AuditHook(AgentHook):
    """每個 LLM call / tool call 都發一筆 AuditEvent."""

    async def after_llm_call(
        self,
        ctx: AgentContext,
        response: LLMResponse,
    ) -> None:
        if ctx.session is None:
            return
        await audit.emit(
            ctx.session,
            event_type="ai.llm_call",
            tenant_id=ctx.tenant_id,
            actor_id=str(ctx.employee_id),
            resource_type="conversation",
            resource_id=str(ctx.conversation_id),
            payload={
                "model": response.model,
                "stop_reason": response.stop_reason,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "tool_use_count": len(response.tool_uses),
                "skill_version_id": (str(ctx.skill_version_id) if ctx.skill_version_id else None),
            },
        )

    async def after_tool_call(
        self,
        ctx: AgentContext,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: Any,
        error: Exception | None = None,
    ) -> None:
        if ctx.session is None:
            return
        await audit.emit(
            ctx.session,
            event_type="ai.tool_call",
            tenant_id=ctx.tenant_id,
            actor_id=str(ctx.employee_id),
            resource_type="tool",
            resource_id=tool_name,
            payload={
                "conversation_id": str(ctx.conversation_id),
                "input_keys": sorted(tool_input.keys()),
                "status": "error" if error is not None else "success",
                "error_message": str(error) if error is not None else None,
            },
        )
