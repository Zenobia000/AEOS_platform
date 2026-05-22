"""request_human_handoff — 建 conversation_handoff row (status=pending).

依 MC-010 §handoff + skills/customer-service/faq-respond/v1.0.0/tools.yaml:
- input: { reason: enum, handoff_message?: str }
- output: { handoff_id: uuid, status: 'pending' }
- 4 種 reason: low_confidence / restricted_tool / user_request / policy_deny
"""

from __future__ import annotations

from typing import Any

from app.agent.tool_executor import ToolExecutionContext
from app.db.models.conversation_handoff import ConversationHandoff

VALID_REASONS = {
    "low_confidence",
    "restricted_tool",
    "user_request",
    "policy_deny",
}


async def request_human_handoff(
    tool_input: dict[str, Any],
    ctx: ToolExecutionContext,
) -> dict[str, str]:
    reason = str(tool_input.get("reason", ""))
    if reason not in VALID_REASONS:
        raise ValueError(f"invalid handoff reason: {reason!r} (allowed: {sorted(VALID_REASONS)})")
    if ctx.conversation_id is None:
        raise ValueError("request_human_handoff requires conversation_id in context")

    handoff_message = tool_input.get("handoff_message")
    handoff = ConversationHandoff(
        from_conversation_id=ctx.conversation_id,
        reason=reason,
        handoff_message=handoff_message,
    )
    ctx.session.add(handoff)
    await ctx.session.flush()

    return {
        "handoff_id": str(handoff.id),
        "status": "pending",
    }
