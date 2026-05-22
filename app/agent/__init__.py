"""Agent runtime layer (MC-009 + ADR-0012 借鑑 nanobot agent).

對外型別：
- `EmployeeRuntime` — Frozen Runtime per conversation turn
- `AgentContext` — single-turn immutable context
- `AgentHook` / `CompositeHook` — interceptor for governance
- 3 預設 hooks: AuditHook / PolicyHook / QuotaHook
"""

from app.agent.context import AgentContext, ToolDecision
from app.agent.hook import AgentHook, CompositeHook
from app.agent.runtime import EmployeeRuntime, TurnResult

__all__ = [
    "AgentContext",
    "AgentHook",
    "CompositeHook",
    "EmployeeRuntime",
    "ToolDecision",
    "TurnResult",
]
