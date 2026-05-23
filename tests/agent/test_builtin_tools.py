"""Built-in tools 行為測試 — search_knowledge / request_human_handoff."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.builtin_tools import register_builtins
from app.agent.builtin_tools.handoff import request_human_handoff
from app.agent.builtin_tools.search_knowledge import search_knowledge
from app.agent.tool_executor import (
    InternalToolRegistry,
    ToolExecutionContext,
)
from app.db.models.conversation import Conversation
from app.db.models.conversation_handoff import ConversationHandoff
from app.db.models.employee import Employee
from app.db.models.knowledge_card import KnowledgeCard
from app.db.models.tenant import Tenant


async def _make_tenant(session: AsyncSession, slug: str) -> Tenant:
    t = Tenant(name=f"T-{slug}", slug=slug)
    session.add(t)
    await session.flush()
    return t


async def _make_conversation(session: AsyncSession, tenant: Tenant) -> Conversation:
    emp = Employee(
        tenant_id=tenant.id,
        name="AI",
        role="customer_service",
        status="draft",
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
        channel_user_id="u",
    )
    session.add(conv)
    await session.flush()
    return conv


def _ctx(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    conversation_id: uuid.UUID | None = None,
) -> ToolExecutionContext:
    return ToolExecutionContext(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        employee_id=uuid.uuid4(),
        skill_version_id=uuid.uuid4(),
        session=session,
    )


# ── register_builtins ───────────────────────────────


def test_register_builtins() -> None:
    reg = InternalToolRegistry()
    register_builtins(reg)
    slugs = set(reg.slugs())
    assert slugs == {"search_knowledge", "request_human_handoff"}


# ── search_knowledge ────────────────────────────────


async def test_search_knowledge_no_embedding_returns_empty(
    db_session: AsyncSession,
) -> None:
    """Phase 1 fallback：input 無 query_embedding → 回空陣列（非 raise）."""
    tenant = await _make_tenant(db_session, "kb-no-emb")
    result = await search_knowledge({"query": "退貨"}, _ctx(db_session, tenant.id))
    assert result == []


async def test_search_knowledge_returns_matching(db_session: AsyncSession) -> None:
    """寫一張 approved KC + 用相同 embedding 查 → 應命中（cosine = 1.0）."""
    tenant = await _make_tenant(db_session, "kb-hit")

    embedding = [1.0] + [0.0] * 1023
    kc = KnowledgeCard(
        tenant_id=tenant.id,
        card_type="faq",
        title="退貨期限",
        body_markdown="商品到貨後 7 天內可申請退貨",
        status="approved",
        embedding=embedding,
    )
    db_session.add(kc)
    await db_session.flush()

    result = await search_knowledge(
        {"query_embedding": embedding, "top_k": 5, "min_score": 0.5},
        _ctx(db_session, tenant.id),
    )

    assert len(result) == 1
    assert result[0]["kc_id"] == str(kc.id)
    assert result[0]["title"] == "退貨期限"
    assert result[0]["score"] >= 0.99


async def test_search_knowledge_filters_drafts(db_session: AsyncSession) -> None:
    """draft KC 不應出現給 LLM."""
    tenant = await _make_tenant(db_session, "kb-draft")
    embedding = [1.0] + [0.0] * 1023
    kc = KnowledgeCard(
        tenant_id=tenant.id,
        card_type="faq",
        title="尚未審核",
        body_markdown="...",
        status="draft",
        embedding=embedding,
    )
    db_session.add(kc)
    await db_session.flush()

    result = await search_knowledge(
        {"query_embedding": embedding},
        _ctx(db_session, tenant.id),
    )
    assert result == []


async def test_search_knowledge_min_score_filter(db_session: AsyncSession) -> None:
    """min_score 提高應過濾掉低相關 KC."""
    tenant = await _make_tenant(db_session, "kb-thresh")
    kc_close = KnowledgeCard(
        tenant_id=tenant.id,
        card_type="faq",
        title="近似",
        body_markdown="x",
        status="approved",
        embedding=[1.0] + [0.0] * 1023,
    )
    kc_far = KnowledgeCard(
        tenant_id=tenant.id,
        card_type="faq",
        title="遠離",
        body_markdown="y",
        status="approved",
        embedding=[0.0] * 1023 + [1.0],
    )
    db_session.add_all([kc_close, kc_far])
    await db_session.flush()

    result = await search_knowledge(
        {
            "query_embedding": [1.0] + [0.0] * 1023,
            "top_k": 5,
            "min_score": 0.95,
        },
        _ctx(db_session, tenant.id),
    )
    ids = {r["kc_id"] for r in result}
    assert str(kc_close.id) in ids
    assert str(kc_far.id) not in ids


# ── request_human_handoff ───────────────────────────


async def test_handoff_creates_pending_row(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "ho-create")
    conv = await _make_conversation(db_session, tenant)

    out = await request_human_handoff(
        {
            "reason": "low_confidence",
            "handoff_message": "AI 不確定，請接手",
        },
        _ctx(db_session, tenant.id, conversation_id=conv.id),
    )

    assert out["status"] == "pending"
    assert uuid.UUID(out["handoff_id"]) is not None

    row = (
        await db_session.execute(
            select(ConversationHandoff).where(ConversationHandoff.from_conversation_id == conv.id)
        )
    ).scalar_one()
    assert row.reason == "low_confidence"
    assert row.handoff_message == "AI 不確定，請接手"
    assert row.to_conversation_id is None


async def test_handoff_invalid_reason_raises(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "ho-bad")
    conv = await _make_conversation(db_session, tenant)
    with pytest.raises(ValueError, match="invalid handoff reason"):
        await request_human_handoff(
            {"reason": "weird"},
            _ctx(db_session, tenant.id, conversation_id=conv.id),
        )


async def test_handoff_requires_conversation_id(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "ho-noconv")
    with pytest.raises(ValueError, match="requires conversation_id"):
        await request_human_handoff(
            {"reason": "user_request"},
            _ctx(db_session, tenant.id, conversation_id=None),
        )
