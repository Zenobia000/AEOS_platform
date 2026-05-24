"""DraftProcessor 寫 message.tool_invocations + kc_refs 整合測試."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import InternalToolRegistry
from app.agent.builtin_tools import register_builtins
from app.db.models.conversation import Conversation
from app.db.models.employee import Employee
from app.db.models.knowledge_card import KnowledgeCard
from app.db.models.tenant import Tenant
from app.db.models.tool import Tool
from app.llm.client import LLMClient, LLMResponse, LLMToolUse, LLMUsage
from app.skill import SkillLoader
from app.worker.draft_processor import (
    DraftProcessor,
    _extract_kc_refs,
    _sanitize_input,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


# ── unit: _extract_kc_refs / _sanitize_input ──


def test_extract_kc_refs_from_search_knowledge() -> None:
    output = [
        {"kc_id": "kc-1", "title": "退貨", "score": 0.9},
        {"kc_id": "kc-2", "title": "保固", "score": 0.85},
    ]
    assert _extract_kc_refs("search_knowledge", output) == ["kc-1", "kc-2"]


def test_extract_kc_refs_non_list_output() -> None:
    assert _extract_kc_refs("search_knowledge", None) == []
    assert _extract_kc_refs("search_knowledge", "string") == []


def test_extract_kc_refs_other_tool_returns_empty() -> None:
    assert _extract_kc_refs("request_human_handoff", [{"kc_id": "x"}]) == []


def test_sanitize_input_removes_query_embedding() -> None:
    sanitized = _sanitize_input({"query": "退貨", "query_embedding": [0.1] * 1024})
    assert "query_embedding" not in sanitized
    assert sanitized["query"] == "退貨"


# ── integration: DraftProcessor writes tool_invocations w/ kc_refs ──


class _StubLLM(LLMClient):
    """單次回應同時帶 text + tool_use（EmployeeRuntime 不會再 re-call）."""

    async def complete(self, **_kwargs: Any) -> LLMResponse:
        return LLMResponse(
            text="您好，退貨可於 7 天內辦理；請保留發票。",
            tool_uses=[
                LLMToolUse(
                    tool_use_id="tu_1",
                    name="search_knowledge",
                    input={"query": "退貨多久"},
                )
            ],
            stop_reason="tool_use",
            usage=LLMUsage(input_tokens=20, output_tokens=30),
            model="fake",
        )


async def _seed_tenant_with_kc(
    session: AsyncSession, *, suffix: str
) -> tuple[Tenant, Conversation, list[KnowledgeCard]]:
    tenant = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}-{suffix}")
    session.add(tenant)
    await session.flush()
    emp = Employee(
        tenant_id=tenant.id,
        name="AI",
        role="customer_service",
        status="live",
        version="1.0.0",
    )
    session.add(emp)
    await session.flush()
    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=emp.id,
        employee_version="1.0.0",
        end_user_pseudo_id="u",
        channel="line",
        channel_user_id=f"U-{suffix}",
    )
    session.add(conv)
    await session.flush()
    # 寫 user message
    await session.execute(
        text(
            "INSERT INTO message (id, conversation_id, seq, role, content, created_at) "
            "VALUES (gen_random_uuid(), :cid, 1, 'user', '退貨多久', NOW())"
        ),
        {"cid": str(conv.id)},
    )
    # 寫 2 張 approved KC（含 embedding）
    embedding = [0.1] * 1024
    kcs: list[KnowledgeCard] = []
    for i in range(2):
        kc = KnowledgeCard(
            tenant_id=tenant.id,
            card_type="policy",
            title=f"退貨 KC {i}",
            body_markdown="退貨可於 7 天內辦理",
            tags=["退貨"],
            status="approved",
            embedding=embedding,
            embedding_model="stub",
        )
        session.add(kc)
        kcs.append(kc)
    await session.flush()
    return tenant, conv, kcs


async def test_draft_processor_records_kc_refs_in_message(
    db_session: AsyncSession,
) -> None:
    _, conv, _ = await _seed_tenant_with_kc(db_session, suffix="kcref")

    # 註冊 tool 進 DB（PolicyHook + ToolExecutor 查 DB tool）
    db_session.add(
        Tool(
            tenant_id=None,
            slug="search_knowledge",
            name="search",
            description="kb search",
            tool_type="internal",
            input_schema={"type": "object"},
            risk_tier="safe",
        )
    )
    await db_session.flush()

    registry = InternalToolRegistry()
    register_builtins(registry)
    proc = DraftProcessor(
        llm=_StubLLM(),
        skill_loader=SkillLoader(root=_repo_root() / "skills"),
        registry=registry,
    )

    # LLM tool call 不帶 query_embedding → search_knowledge 回 []，但 tool_invocations
    # 仍會記錄該次呼叫。
    result = await proc.process_message(
        session=db_session,
        conversation_id=conv.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )
    assert result.outbound_message_id is not None

    rows = (
        await db_session.execute(
            text(
                "SELECT tool_invocations FROM message "
                "WHERE conversation_id = :cid AND role = 'assistant' "
                "ORDER BY seq DESC LIMIT 1"
            ),
            {"cid": str(conv.id)},
        )
    ).first()
    assert rows is not None
    ti = rows[0]
    assert isinstance(ti, list)
    assert len(ti) == 1
    assert ti[0]["name"] == "search_knowledge"
    assert ti[0]["ok"] is True
    assert "query_embedding" not in ti[0]["input"]  # sanitized
