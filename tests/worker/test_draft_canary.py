"""DraftProcessor canary 路由整合測試 — outbound_initial_status 受 percent 影響."""

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
from app.db.models.outbound_message import OutboundMessage
from app.db.models.tenant import Tenant
from app.llm.client import LLMClient, LLMResponse, LLMUsage
from app.services import canary
from app.skill import SkillLoader
from app.worker.draft_processor import DraftProcessor


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class _FakeLLM(LLMClient):
    async def complete(self, **_kwargs: Any) -> LLMResponse:
        return LLMResponse(
            text="您好，本店退貨可於 7 天內申請",
            tool_uses=[],
            stop_reason="end_turn",
            usage=LLMUsage(input_tokens=5, output_tokens=15),
            model="fake",
        )


async def _seed_conv_with_user_msg(
    session: AsyncSession, *, suffix: str
) -> tuple[Tenant, Conversation]:
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
    await session.execute(
        text(
            "INSERT INTO message (id, conversation_id, seq, role, content, created_at) "
            "VALUES (gen_random_uuid(), :cid, 1, 'user', '退貨多久', NOW())"
        ),
        {"cid": str(conv.id)},
    )
    await session.flush()
    return tenant, conv


def _make_processor() -> DraftProcessor:
    registry = InternalToolRegistry()
    register_builtins(registry)
    return DraftProcessor(
        llm=_FakeLLM(),
        skill_loader=SkillLoader(root=_repo_root() / "skills"),
        registry=registry,
        # outbound_initial_status=None → 使用 canary 決定
    )


async def test_canary_zero_routes_to_awaiting_review(
    db_session: AsyncSession,
) -> None:
    """預設 0% canary → 全 Draft Mode."""
    _, conv = await _seed_conv_with_user_msg(db_session, suffix="z")
    proc = _make_processor()

    result = await proc.process_message(
        session=db_session,
        conversation_id=conv.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )
    assert result.outbound_message_id is not None

    out = await db_session.get(OutboundMessage, result.outbound_message_id)
    assert out is not None
    assert out.status == "awaiting_review"


async def test_canary_100_routes_to_pending(db_session: AsyncSession) -> None:
    """100% canary → 全 auto-reply（pending）."""
    tenant, conv = await _seed_conv_with_user_msg(db_session, suffix="h")
    await canary.set_canary_percent(
        db_session,
        tenant_id=tenant.id,
        percent=100,
        actor_id="cto",
        reason="full auto",
    )
    proc = _make_processor()
    result = await proc.process_message(
        session=db_session,
        conversation_id=conv.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )
    out = await db_session.get(OutboundMessage, result.outbound_message_id)
    assert out is not None
    assert out.status == "pending"


async def test_force_initial_status_overrides_canary(
    db_session: AsyncSession,
) -> None:
    """構造時傳 outbound_initial_status 強制覆寫 canary 決策."""
    tenant, conv = await _seed_conv_with_user_msg(db_session, suffix="force")
    # 即使 canary 設 100，強制 awaiting_review 應贏
    await canary.set_canary_percent(
        db_session,
        tenant_id=tenant.id,
        percent=100,
        actor_id="x",
        reason="r",
    )

    registry = InternalToolRegistry()
    register_builtins(registry)
    proc = DraftProcessor(
        llm=_FakeLLM(),
        skill_loader=SkillLoader(root=_repo_root() / "skills"),
        registry=registry,
        outbound_initial_status="awaiting_review",
    )
    result = await proc.process_message(
        session=db_session,
        conversation_id=conv.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )
    out = await db_session.get(OutboundMessage, result.outbound_message_id)
    assert out is not None
    assert out.status == "awaiting_review"
