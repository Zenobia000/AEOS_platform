"""DraftProcessor 對 kill switch 的反應 — 跳過 LLM + 建 handoff + audit."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import InternalToolRegistry
from app.agent.builtin_tools import register_builtins
from app.db.models.audit_log import AuditLog
from app.db.models.conversation import Conversation
from app.db.models.conversation_handoff import ConversationHandoff
from app.db.models.employee import Employee
from app.db.models.outbound_message import OutboundMessage
from app.db.models.tenant import Tenant
from app.llm.client import LLMClient, LLMResponse, LLMUsage
from app.services import kill_switch
from app.skill import SkillLoader
from app.worker.draft_processor import DraftProcessor


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class _FakeLLM(LLMClient):
    def __init__(self) -> None:
        self.called = False

    async def complete(self, **_kwargs: Any) -> LLMResponse:
        self.called = True
        return LLMResponse(
            text="should not be reached",
            tool_uses=[],
            stop_reason="end_turn",
            usage=LLMUsage(input_tokens=1, output_tokens=1),
        )


async def _seed(db_session: AsyncSession) -> tuple[Tenant, Conversation]:
    tenant = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}-ks")
    db_session.add(tenant)
    await db_session.flush()
    emp = Employee(
        tenant_id=tenant.id,
        name="AI",
        role="customer_service",
        status="live",
        version="1.0.0",
    )
    db_session.add(emp)
    await db_session.flush()
    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=emp.id,
        employee_version="1.0.0",
        end_user_pseudo_id="u",
        channel="line",
        channel_user_id="U-ks",
    )
    db_session.add(conv)
    await db_session.flush()
    return tenant, conv


async def test_kill_switch_disabled_skips_llm_and_creates_handoff(
    db_session: AsyncSession,
) -> None:
    tenant, conv = await _seed(db_session)
    await kill_switch.disable_ai(
        db_session,
        tenant_id=tenant.id,
        confirm_tenant_id=tenant.id,
        actor_id="cto",
        reason="incident smoke",
    )

    fake_llm = _FakeLLM()
    registry = InternalToolRegistry()
    register_builtins(registry)
    proc = DraftProcessor(
        llm=fake_llm,
        skill_loader=SkillLoader(root=_repo_root() / "skills"),
        registry=registry,
    )

    result = await proc.process_message(
        session=db_session,
        conversation_id=conv.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )

    assert fake_llm.called is False  # LLM 沒被呼叫
    assert result.assistant_text == ""
    assert result.outbound_message_id is None  # 沒寫 outbound

    handoff = (
        await db_session.execute(
            select(ConversationHandoff).where(ConversationHandoff.from_conversation_id == conv.id)
        )
    ).scalar_one()
    assert handoff.reason == "policy_deny"

    audit_row = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.event_type == "kill_switch.intercepted")
        )
    ).scalar_one()
    assert audit_row.resource_id == str(conv.id)

    # outbound 表完全沒新增
    outbounds = (
        (
            await db_session.execute(
                select(OutboundMessage).where(OutboundMessage.conversation_id == conv.id)
            )
        )
        .scalars()
        .all()
    )
    assert list(outbounds) == []
