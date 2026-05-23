"""DraftProcessor 整合測試 — fake LLM + 真實 DB + SkillLoader."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import InternalToolRegistry
from app.agent.builtin_tools import register_builtins
from app.db.models.audit_log import AuditLog
from app.db.models.conversation import Conversation
from app.db.models.employee import Employee
from app.db.models.outbound_message import OutboundMessage
from app.db.models.tenant import Tenant
from app.db.models.tool import Tool
from app.llm.client import LLMClient, LLMMessage, LLMResponse, LLMToolUse, LLMUsage
from app.skill import SkillLoader
from app.worker.draft_processor import DraftProcessor


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class _FakeLLM(LLMClient):
    """可預設 response + 記錄 last call kwargs。"""

    def __init__(self, response: LLMResponse) -> None:
        self.response = response
        self.last_kwargs: dict[str, Any] = {}

    async def complete(self, **kwargs: Any) -> LLMResponse:
        self.last_kwargs = kwargs
        return self.response


async def _seed_conv(
    session: AsyncSession,
    *,
    user_text: str = "請問退貨期限",
) -> tuple[Tenant, Employee, Conversation]:
    tenant = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}")
    session.add(tenant)
    await session.flush()
    employee = Employee(
        tenant_id=tenant.id,
        name="AI CS",
        role="customer_service",
        status="live",
        version="1.0.0",
    )
    session.add(employee)
    await session.flush()
    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=employee.id,
        employee_version="1.0.0",
        end_user_pseudo_id="pseudo-u",
        channel="line",
        channel_user_id="U-line-1",
    )
    session.add(conv)
    await session.flush()

    # 寫一則 user message
    await session.execute(
        text(
            "INSERT INTO message "
            "(id, conversation_id, seq, role, content, created_at) "
            "VALUES (gen_random_uuid(), :cid, 1, 'user', :c, NOW())"
        ),
        {"cid": str(conv.id), "c": user_text},
    )
    await session.execute(
        text(
            "UPDATE conversation SET message_count = 1, last_message_at = NOW(), "
            "status = 'active' WHERE id = :cid"
        ),
        {"cid": str(conv.id)},
    )
    await session.refresh(conv)
    return tenant, employee, conv


def _make_processor(llm: LLMClient) -> DraftProcessor:
    registry = InternalToolRegistry()
    register_builtins(registry)
    return DraftProcessor(
        llm=llm,
        skill_loader=SkillLoader(root=_repo_root() / "skills"),
        registry=registry,
    )


async def test_process_message_writes_assistant_and_outbound(
    db_session: AsyncSession,
) -> None:
    tenant, _employee, conv = await _seed_conv(db_session)

    fake_resp = LLMResponse(
        text="您好，本店退貨期限為到貨後 7 天內。",
        usage=LLMUsage(input_tokens=150, output_tokens=30),
        model="claude-sonnet-4-6",
    )
    proc = _make_processor(_FakeLLM(fake_resp))

    result = await proc.process_message(
        session=db_session,
        conversation_id=conv.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )

    assert result.conversation_id == conv.id
    assert "退貨期限" in result.assistant_text
    assert result.outbound_message_id is not None

    # assistant message 寫進 message 表
    msgs = (
        await db_session.execute(
            text(
                "SELECT role, content, seq, token_count FROM message "
                "WHERE conversation_id = :cid ORDER BY seq"
            ),
            {"cid": str(conv.id)},
        )
    ).all()
    assert len(msgs) == 2
    assert msgs[0][0] == "user"
    assert msgs[1][0] == "assistant"
    assert "退貨期限" in msgs[1][1]
    assert msgs[1][2] == 2  # seq
    assert msgs[1][3] == 30  # output_tokens

    # outbound_message row
    out = (
        await db_session.execute(
            select(OutboundMessage).where(OutboundMessage.id == result.outbound_message_id)
        )
    ).scalar_one()
    # S5 canary 預設 0% → 'awaiting_review' (Draft Mode)
    assert out.status == "awaiting_review"
    assert out.channel == "line"
    assert out.tenant_id == tenant.id

    # conversation counter +1 (現在 = 2)
    await db_session.refresh(conv)
    assert conv.message_count == 2


async def test_process_passes_skill_system_prompt(db_session: AsyncSession) -> None:
    """system prompt 應從 skills/customer-service/faq-respond/v1.0.0/system.md 載入後傳給 LLM."""
    _, _, conv = await _seed_conv(db_session)
    llm = _FakeLLM(LLMResponse(text="ok", usage=LLMUsage(input_tokens=10, output_tokens=5)))
    proc = _make_processor(llm)

    await proc.process_message(
        session=db_session,
        conversation_id=conv.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )

    sys = llm.last_kwargs.get("system")
    assert sys is not None
    assert "AI 客服" in sys or "客服" in sys


async def test_process_passes_tool_definitions(db_session: AsyncSession) -> None:
    """skill.tool_bindings 應轉成 LLM tools 參數."""
    _, _, conv = await _seed_conv(db_session)
    llm = _FakeLLM(LLMResponse(text="ok", usage=LLMUsage(input_tokens=10, output_tokens=5)))
    proc = _make_processor(llm)

    await proc.process_message(
        session=db_session,
        conversation_id=conv.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )

    tools = llm.last_kwargs.get("tools") or []
    names = {t.name for t in tools}
    assert "search_knowledge" in names
    assert "request_human_handoff" in names


async def test_process_history_passed_chronologically(db_session: AsyncSession) -> None:
    """history 多則訊息應按 seq asc 傳給 LLM."""
    _, _, conv = await _seed_conv(db_session, user_text="第一則")
    # 再加一則 user
    await db_session.execute(
        text(
            "INSERT INTO message (id, conversation_id, seq, role, content, created_at) "
            "VALUES (gen_random_uuid(), :cid, 2, 'user', '第二則', NOW())"
        ),
        {"cid": str(conv.id)},
    )
    await db_session.execute(
        text("UPDATE conversation SET message_count = 2 WHERE id = :cid"),
        {"cid": str(conv.id)},
    )

    llm = _FakeLLM(LLMResponse(text="ok", usage=LLMUsage(input_tokens=10, output_tokens=5)))
    proc = _make_processor(llm)
    await proc.process_message(
        session=db_session,
        conversation_id=conv.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )

    msgs: list[LLMMessage] = list(llm.last_kwargs["messages"])
    assert [m.content for m in msgs] == ["第一則", "第二則"]
    assert [m.role for m in msgs] == ["user", "user"]


async def test_process_handles_tool_use(db_session: AsyncSession) -> None:
    """LLM 回 tool_use → ToolExecutor 跑（builtin search_knowledge）→ 寫 tool_invocation row.

    search_knowledge handler 因 query_embedding 缺會回空，但 tool 仍會被執行
    + tool_invocation 仍會被寫（status=success, output=[]）.
    """
    _, _, conv = await _seed_conv(db_session)

    # 先在 DB 註冊 tool（PolicyHook 與 ToolExecutor 都查 DB tool）
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

    fake_resp = LLMResponse(
        text="讓我查一下",
        tool_uses=[
            LLMToolUse(
                tool_use_id="t1",
                name="search_knowledge",
                input={"query": "退貨", "top_k": 5},
            )
        ],
        usage=LLMUsage(input_tokens=100, output_tokens=20),
        stop_reason="tool_use",
    )
    proc = _make_processor(_FakeLLM(fake_resp))
    result = await proc.process_message(
        session=db_session,
        conversation_id=conv.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )

    assert len(result.turn_result.tool_calls) == 1
    rec = result.turn_result.tool_calls[0]
    assert rec.tool_name == "search_knowledge"
    assert rec.decision.is_allowed is True

    # tool_invocation row 應寫入
    from app.db.models.tool_invocation import ToolInvocation

    invs = (
        (
            await db_session.execute(
                select(ToolInvocation).where(ToolInvocation.tenant_id == conv.tenant_id)
            )
        )
        .scalars()
        .all()
    )
    assert len(invs) == 1
    assert invs[0].status == "success"


async def test_process_empty_response_no_outbound(db_session: AsyncSession) -> None:
    """LLM 回空字串（極端情境）→ 不該建 outbound_message."""
    _, _, conv = await _seed_conv(db_session)
    llm = _FakeLLM(LLMResponse(text="", usage=LLMUsage(input_tokens=5, output_tokens=0)))
    proc = _make_processor(llm)

    result = await proc.process_message(
        session=db_session,
        conversation_id=conv.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )

    assert result.outbound_message_id is None
    outs = (
        (
            await db_session.execute(
                select(OutboundMessage).where(OutboundMessage.conversation_id == conv.id)
            )
        )
        .scalars()
        .all()
    )
    assert outs == []


async def test_process_with_audit_hook(db_session: AsyncSession) -> None:
    """注入 AuditHook → after_llm_call 寫 ai.llm_call 事件."""
    from app.agent.hooks.audit import AuditHook

    _, _, conv = await _seed_conv(db_session)
    fake_resp = LLMResponse(
        text="ok",
        usage=LLMUsage(input_tokens=50, output_tokens=20),
        model="claude-sonnet-4-6",
    )
    registry = InternalToolRegistry()
    register_builtins(registry)
    proc = DraftProcessor(
        llm=_FakeLLM(fake_resp),
        skill_loader=SkillLoader(root=_repo_root() / "skills"),
        registry=registry,
        hook=AuditHook(),
    )

    await proc.process_message(
        session=db_session,
        conversation_id=conv.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )

    audits = (
        (await db_session.execute(select(AuditLog).where(AuditLog.event_type == "ai.llm_call")))
        .scalars()
        .all()
    )
    assert len(audits) == 1
    assert audits[0].payload["model"] == "claude-sonnet-4-6"
    assert audits[0].payload["input_tokens"] == 50
