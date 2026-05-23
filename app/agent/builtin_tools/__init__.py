"""Built-in tools (internal handlers) — Phase 1 預設 2 個.

對應 skills/customer-service/faq-respond/v1.0.0/tools.yaml：
- search_knowledge — RAG over knowledge_card via pgvector
- request_human_handoff — 建 conversation_handoff row (pending)

註冊方式：
    registry = InternalToolRegistry()
    register_builtins(registry)
    executor = ToolExecutor(registry=registry)
"""

from app.agent.builtin_tools.handoff import request_human_handoff
from app.agent.builtin_tools.search_knowledge import search_knowledge
from app.agent.tool_executor import InternalToolRegistry


def register_builtins(registry: InternalToolRegistry) -> None:
    """把 Phase 1 兩個 tool handler 註冊進 registry."""
    registry.register("search_knowledge", search_knowledge)
    registry.register("request_human_handoff", request_human_handoff)


__all__ = ["register_builtins", "request_human_handoff", "search_knowledge"]
