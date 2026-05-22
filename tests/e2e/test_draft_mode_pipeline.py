"""Draft Mode 端到端 smoke test — inbound → AI draft → expert approve → LINE Push.

驗證 PRD-001 §5.4 (Draft Mode) 完整鏈路是否串得起來，不關注每個元件的內部
細節（個別元件由各自單元測試覆蓋）。

鏈路：
1. seed tenant + employee + channel_binding + conversation + user message
2. DraftProcessor(outbound_initial_status='awaiting_review') + fake LLM
   → INSERT outbound_message (awaiting_review)
3. expert_review.list_pending → 看到該 outbound
4. expert_review.approve → 狀態 → 'pending'
5. OutboundProcessor + mock LINE Push (200 OK) → 狀態 → 'sent'

斷言：
- outbound 狀態演進完整
- LINE Push HTTP body 帶到 expert 同意送出的 draft 文字
- audit log 序列：expert.draft_approved → channel.message_pushed
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import InternalToolRegistry
from app.agent.builtin_tools import register_builtins
from app.db.models.audit_log import AuditLog
from app.db.models.channel_binding import ChannelBinding
from app.db.models.conversation import Conversation
from app.db.models.employee import Employee
from app.db.models.outbound_message import OutboundMessage
from app.db.models.tenant import Tenant
from app.llm.client import LLMClient, LLMResponse, LLMUsage
from app.services import expert_review
from app.skill import SkillLoader
from app.worker.draft_processor import DraftProcessor
from app.worker.outbound_processor import OutboundProcessor

LINE_TOKEN = "channel-access-token-e2e"
DRAFT_TEXT = "您好，本店退貨可於到貨後 7 天內申請；請保留發票"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class _FixedLLM(LLMClient):
    def __init__(self, text_response: str) -> None:
        self._text = text_response

    async def complete(self, **_kwargs: Any) -> LLMResponse:
        return LLMResponse(
            text=self._text,
            tool_uses=[],
            stop_reason="end_turn",
            usage=LLMUsage(input_tokens=10, output_tokens=20),
        )


async def _seed_inbound(
    session: AsyncSession,
    *,
    user_text: str,
) -> tuple[Tenant, Employee, Conversation]:
    tenant = Tenant(name="Acme E2E", slug=f"acme-{uuid.uuid4().hex[:6]}")
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
    session.add(
        ChannelBinding(
            employee_id=employee.id,
            channel="line",
            config={"channel_id": "U-line-e2e", "channel_access_token": LINE_TOKEN},
            enabled=True,
        )
    )
    await session.flush()
    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=employee.id,
        employee_version="1.0.0",
        end_user_pseudo_id="pseudo-e2e",
        channel="line",
        channel_user_id="U-end-user-e2e",
    )
    session.add(conv)
    await session.flush()
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
            "UPDATE conversation SET message_count = 1, status = 'active', "
            "last_message_at = NOW() WHERE id = :cid"
        ),
        {"cid": str(conv.id)},
    )
    await session.refresh(conv)
    return tenant, employee, conv


def _make_draft_processor(llm: LLMClient) -> DraftProcessor:
    registry = InternalToolRegistry()
    register_builtins(registry)
    return DraftProcessor(
        llm=llm,
        skill_loader=SkillLoader(root=_repo_root() / "skills"),
        registry=registry,
        outbound_initial_status="awaiting_review",
    )


async def test_inbound_to_push_full_draft_mode_chain(db_session: AsyncSession) -> None:
    # 1. seed inbound user message
    tenant, _, conv = await _seed_inbound(db_session, user_text="請問退貨幾天內")

    # 2. DraftProcessor → outbound in awaiting_review
    proc = _make_draft_processor(_FixedLLM(DRAFT_TEXT))
    draft = await proc.process_message(
        session=db_session,
        conversation_id=conv.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )
    assert draft.assistant_text == DRAFT_TEXT
    assert draft.outbound_message_id is not None

    outbound = (
        await db_session.execute(
            select(OutboundMessage).where(OutboundMessage.id == draft.outbound_message_id)
        )
    ).scalar_one()
    assert outbound.status == "awaiting_review"

    # 3. expert sees it in queue
    pending = await expert_review.list_pending(db_session, tenant_id=tenant.id)
    assert len(pending) == 1
    assert pending[0]["outbound_id"] == str(outbound.id)
    assert pending[0]["draft_text"] == DRAFT_TEXT

    # 4. expert approves → 'pending'
    approve_result = await expert_review.approve(
        db_session,
        outbound_id=outbound.id,
        expert_id="expert-e2e",
    )
    assert approve_result.new_status == "pending"

    await db_session.refresh(outbound)
    assert outbound.status == "pending"

    # 5. OutboundProcessor mocks LINE Push 200 → 'sent'
    captured: dict[str, Any] = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        import json as _json

        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        captured["body"] = _json.loads(request.content.decode())
        return httpx.Response(200, json={})

    transport = httpx.MockTransport(_handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        op = OutboundProcessor(http_client=http_client)
        push_result = await op.process_one(db_session, outbound)

    assert push_result.status == "sent"
    assert captured["url"] == "https://api.line.me/v2/bot/message/push"
    assert captured["auth"] == f"Bearer {LINE_TOKEN}"
    assert captured["body"]["to"] == "U-end-user-e2e"
    assert captured["body"]["messages"][0]["text"] == DRAFT_TEXT

    await db_session.refresh(outbound)
    assert outbound.status == "sent"
    assert outbound.sent_at is not None

    # 6. audit trail：兩個關鍵事件都在
    approved = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.event_type == "expert.draft_approved")
        )
    ).scalar_one()
    assert approved.actor_id == "expert-e2e"

    pushed = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.event_type == "channel.message_pushed")
        )
    ).scalar_one()
    assert pushed.resource_id == str(outbound.id)

    # 7. queue 已清空
    remaining = await expert_review.list_pending(db_session, tenant_id=tenant.id)
    assert remaining == []


async def test_reject_path_stops_pipeline_and_creates_handoff(
    db_session: AsyncSession,
) -> None:
    """Draft Mode 拒絕路徑：reject 後不應該被 OutboundProcessor 撿到。"""
    _, _, conv = await _seed_inbound(db_session, user_text="退貨怎麼辦")

    proc = _make_draft_processor(_FixedLLM(DRAFT_TEXT))
    draft = await proc.process_message(
        session=db_session,
        conversation_id=conv.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )
    assert draft.outbound_message_id is not None
    outbound_id = draft.outbound_message_id

    reject = await expert_review.reject(
        db_session,
        outbound_id=outbound_id,
        reason="AI 答案不夠精準",
        expert_id="expert-e2e",
        handoff_message="請接手",
    )
    assert reject.handoff_id is not None

    # 仍可查到 outbound row（為了 audit），但 status 是 rejected
    outbound = (
        await db_session.execute(select(OutboundMessage).where(OutboundMessage.id == outbound_id))
    ).scalar_one()
    assert outbound.status == "rejected"

    # OutboundProcessor 的 pending claim 邏輯應該不會抓到 rejected
    # 直接驗證 partial index 範圍：status IN ('pending', 'retrying') 不含 rejected
    pending_count = (
        await db_session.execute(
            text(
                "SELECT COUNT(*) FROM outbound_message "
                "WHERE status IN ('pending', 'retrying') AND id = :oid"
            ),
            {"oid": str(outbound_id)},
        )
    ).scalar_one()
    assert pending_count == 0
