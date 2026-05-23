"""Worker main loop 行為測試 — pollers + iteration + stop event."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.agent import InternalToolRegistry
from app.agent.builtin_tools import register_builtins
from app.db.models.channel_binding import ChannelBinding
from app.db.models.conversation import Conversation
from app.db.models.employee import Employee
from app.db.models.outbound_message import OutboundMessage
from app.db.models.tenant import Tenant
from app.llm.client import LLMClient, LLMResponse, LLMUsage
from app.skill import SkillLoader
from app.worker.draft_processor import DraftProcessor
from app.worker.loop import (
    find_conversation_needing_draft,
    find_pending_outbound,
    run_iteration,
    run_loop,
)
from app.worker.outbound_processor import OutboundProcessor


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class _FakeLLM(LLMClient):
    def __init__(self, text_response: str = "您好") -> None:
        self.text_response = text_response
        self.call_count = 0

    async def complete(self, **kwargs: Any) -> LLMResponse:
        self.call_count += 1
        return LLMResponse(
            text=self.text_response,
            usage=LLMUsage(input_tokens=10, output_tokens=5),
            model="claude-sonnet-4-6",
        )


async def _seed_user_message(
    session: AsyncSession,
    *,
    slug_suffix: str = "x",
    last_role: str = "user",
) -> Conversation:
    """建 tenant + employee + binding + conversation + 一則 message (role=last_role)."""
    tenant = Tenant(name="T", slug=f"t-{slug_suffix}-{uuid.uuid4().hex[:6]}")
    session.add(tenant)
    await session.flush()
    employee = Employee(
        tenant_id=tenant.id,
        name="AI",
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
            config={"channel_id": f"U-{slug_suffix}", "channel_access_token": "tok"},
        )
    )
    await session.flush()
    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=employee.id,
        employee_version="1.0.0",
        end_user_pseudo_id="u",
        channel="line",
        channel_user_id="U-end-1",
        status="active",
    )
    session.add(conv)
    await session.flush()
    await session.execute(
        text(
            "INSERT INTO message (id, conversation_id, seq, role, content, created_at) "
            "VALUES (gen_random_uuid(), :cid, 1, :r, '問題', NOW())"
        ),
        {"cid": str(conv.id), "r": last_role},
    )
    await session.execute(
        text("UPDATE conversation SET message_count = 1, last_message_at = NOW() WHERE id = :cid"),
        {"cid": str(conv.id)},
    )
    return conv


def _make_processors(
    llm: LLMClient,
    http_client: httpx.AsyncClient,
) -> tuple[DraftProcessor, OutboundProcessor]:
    registry = InternalToolRegistry()
    register_builtins(registry)
    draft = DraftProcessor(
        llm=llm,
        skill_loader=SkillLoader(root=_repo_root() / "skills"),
        registry=registry,
    )
    out = OutboundProcessor(http_client=http_client)
    return draft, out


# ── Pollers ─────────────────────────────────────────


async def test_find_draft_target_picks_user_last(db_session: AsyncSession) -> None:
    conv = await _seed_user_message(db_session, slug_suffix="draft", last_role="user")

    ids = await find_conversation_needing_draft(db_session, limit=5)
    assert conv.id in ids


async def test_find_draft_target_skips_assistant_last(db_session: AsyncSession) -> None:
    """最後一則 message 是 assistant → 不被選."""
    await _seed_user_message(db_session, slug_suffix="ai-last", last_role="assistant")
    ids = await find_conversation_needing_draft(db_session, limit=5)
    assert ids == []


async def test_find_draft_target_skips_archived(db_session: AsyncSession) -> None:
    conv = await _seed_user_message(db_session, slug_suffix="archived")
    await db_session.execute(
        text("UPDATE conversation SET status='archived' WHERE id = :cid"),
        {"cid": str(conv.id)},
    )
    ids = await find_conversation_needing_draft(db_session, limit=5)
    assert conv.id not in ids


async def test_find_pending_outbound(db_session: AsyncSession) -> None:
    conv = await _seed_user_message(db_session, slug_suffix="out-pend")
    # 加一筆 pending outbound
    out = OutboundMessage(
        tenant_id=conv.tenant_id,
        conversation_id=conv.id,
        message_id=uuid.uuid4(),
        channel="line",
        channel_user_id="U-end-1",
        status="pending",
    )
    db_session.add(out)
    await db_session.flush()

    pending = await find_pending_outbound(db_session, limit=5)
    ids = {p.id for p in pending}
    assert out.id in ids


async def test_find_pending_outbound_includes_retrying(db_session: AsyncSession) -> None:
    conv = await _seed_user_message(db_session, slug_suffix="out-retry")
    out = OutboundMessage(
        tenant_id=conv.tenant_id,
        conversation_id=conv.id,
        message_id=uuid.uuid4(),
        channel="line",
        channel_user_id="u",
        status="retrying",
        retry_count=1,
    )
    db_session.add(out)
    await db_session.flush()

    pending = await find_pending_outbound(db_session, limit=5)
    assert out.id in {p.id for p in pending}


async def test_find_pending_outbound_skips_sent_failed(db_session: AsyncSession) -> None:
    conv = await _seed_user_message(db_session, slug_suffix="out-sent")
    out_sent = OutboundMessage(
        tenant_id=conv.tenant_id,
        conversation_id=conv.id,
        message_id=uuid.uuid4(),
        channel="line",
        channel_user_id="u",
        status="sent",
    )
    out_failed = OutboundMessage(
        tenant_id=conv.tenant_id,
        conversation_id=conv.id,
        message_id=uuid.uuid4(),
        channel="line",
        channel_user_id="u",
        status="failed",
    )
    db_session.add_all([out_sent, out_failed])
    await db_session.flush()

    pending = await find_pending_outbound(db_session, limit=5)
    found_ids = {p.id for p in pending}
    assert out_sent.id not in found_ids
    assert out_failed.id not in found_ids


# ── run_iteration ───────────────────────────────────


async def test_iteration_processes_draft_then_outbound(db_session: AsyncSession) -> None:
    """完整一回合：user msg → DraftProcessor → outbound_message → OutboundProcessor."""
    conv = await _seed_user_message(db_session, slug_suffix="full-iter")

    llm = _FakeLLM(text_response="您好，本店退貨 7 天內")
    transport = httpx.MockTransport(lambda _req: httpx.Response(200, json={}))
    async with httpx.AsyncClient(transport=transport) as client:
        draft, outbound = _make_processors(llm, client)
        result = await run_iteration(
            db_session,
            draft_processor=draft,
            outbound_processor=outbound,
        )

    assert result.drafts_processed == 1
    assert result.outbounds_processed == 1
    assert result.drafts_failed == 0
    assert result.outbounds_failed == 0
    assert result.did_work is True

    # 該 conversation 現在最後一則是 assistant
    last_role = (
        await db_session.execute(
            text("SELECT role FROM message WHERE conversation_id = :cid ORDER BY seq DESC LIMIT 1"),
            {"cid": str(conv.id)},
        )
    ).scalar_one()
    assert last_role == "assistant"


async def test_iteration_no_work_returns_zero(db_session: AsyncSession) -> None:
    llm = _FakeLLM()
    transport = httpx.MockTransport(lambda _req: httpx.Response(200))
    async with httpx.AsyncClient(transport=transport) as client:
        draft, outbound = _make_processors(llm, client)
        result = await run_iteration(
            db_session,
            draft_processor=draft,
            outbound_processor=outbound,
        )
    assert result.drafts_processed == 0
    assert result.outbounds_processed == 0
    assert result.did_work is False
    assert llm.call_count == 0


async def test_iteration_isolates_draft_failure(db_session: AsyncSession) -> None:
    """LLM raise → drafts_failed++，後續 outbound 仍跑."""
    await _seed_user_message(db_session, slug_suffix="fail-draft")

    class _BoomLLM(LLMClient):
        async def complete(self, **kwargs: Any) -> LLMResponse:
            raise RuntimeError("LLM API down")

    transport = httpx.MockTransport(lambda _req: httpx.Response(200))
    async with httpx.AsyncClient(transport=transport) as client:
        draft, outbound = _make_processors(_BoomLLM(), client)
        result = await run_iteration(
            db_session,
            draft_processor=draft,
            outbound_processor=outbound,
            max_drafts_per_iter=1,  # 只試一次
        )

    assert result.drafts_failed == 1
    assert result.drafts_processed == 0


async def test_iteration_respects_max_per_iter(db_session: AsyncSession) -> None:
    """max_drafts_per_iter 限制一次最多處理幾筆."""
    for i in range(3):
        await _seed_user_message(db_session, slug_suffix=f"multi-{i}")

    llm = _FakeLLM()
    transport = httpx.MockTransport(lambda _req: httpx.Response(200))
    async with httpx.AsyncClient(transport=transport) as client:
        draft, outbound = _make_processors(llm, client)
        result = await run_iteration(
            db_session,
            draft_processor=draft,
            outbound_processor=outbound,
            max_drafts_per_iter=2,
        )

    assert result.drafts_processed == 2


# ── run_loop ────────────────────────────────────────


async def test_run_loop_stops_on_event(db_engine: AsyncEngine) -> None:
    """run_loop 收到 stop event 應立即離開."""
    sm = async_sessionmaker(bind=db_engine, expire_on_commit=False)

    llm = _FakeLLM()
    transport = httpx.MockTransport(lambda _req: httpx.Response(200))
    async with httpx.AsyncClient(transport=transport) as client:
        draft, outbound = _make_processors(llm, client)
        stop = asyncio.Event()

        async def _trigger_stop() -> None:
            await asyncio.sleep(0.05)
            stop.set()

        await asyncio.gather(
            run_loop(
                sm,
                draft_processor=draft,
                outbound_processor=outbound,
                interval_s=0.02,
                stop_event=stop,
            ),
            _trigger_stop(),
        )

    # 沒 hang；測試走完即成功
    assert stop.is_set()


async def test_run_loop_processes_pending_work(db_engine: AsyncEngine) -> None:
    """run_loop 跑時應撿到 pending user message + 寫 assistant + outbound."""
    sm = async_sessionmaker(bind=db_engine, expire_on_commit=False)

    # seed
    async with sm() as setup_session:
        await setup_session.begin()
        await _seed_user_message(setup_session, slug_suffix="loop-pick")
        await setup_session.commit()

    llm = _FakeLLM(text_response="收到")
    transport = httpx.MockTransport(lambda _req: httpx.Response(200, json={}))

    async with httpx.AsyncClient(transport=transport) as client:
        draft, outbound = _make_processors(llm, client)
        stop = asyncio.Event()

        async def _stop_after_one_cycle() -> None:
            await asyncio.sleep(0.1)  # 給 loop 跑至少一輪
            stop.set()

        await asyncio.gather(
            run_loop(
                sm,
                draft_processor=draft,
                outbound_processor=outbound,
                interval_s=0.05,
                stop_event=stop,
            ),
            _stop_after_one_cycle(),
        )

    # 驗證已處理
    async with sm() as check:
        assistant_count = (
            await check.execute(text("SELECT COUNT(*) FROM message WHERE role = 'assistant'"))
        ).scalar_one()
        assert assistant_count >= 1

        sent_count = (
            await check.execute(text("SELECT COUNT(*) FROM outbound_message WHERE status = 'sent'"))
        ).scalar_one()
        assert sent_count >= 1
