"""L2.5 Session Summary service tests (Phase 1 後續 #12)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.conversation import Conversation
from app.db.models.employee import Employee
from app.db.models.tenant import Tenant
from app.llm.client import LLMClient, LLMResponse, LLMUsage
from app.services.session_summary import (
    _summarize_stub,
    generate_summary,
    write_summary_to_conversation,
)


class _FakeLLM(LLMClient):
    def __init__(self, text: str) -> None:
        self.response_text = text
        self.calls: list[dict[str, Any]] = []

    async def complete(self, **kwargs: Any) -> LLMResponse:
        self.calls.append(kwargs)
        return LLMResponse(
            text=self.response_text,
            usage=LLMUsage(input_tokens=100, output_tokens=50),
        )


async def _seed_conv_with_msgs(session: AsyncSession, msgs: list[tuple[str, str]]) -> uuid.UUID:
    t = Tenant(name="T", slug=f"ss-{uuid.uuid4().hex[:6]}")
    session.add(t)
    await session.flush()
    e = Employee(
        tenant_id=t.id, name="AI", role="customer_service", status="draft", version="1.0.0"
    )
    session.add(e)
    await session.flush()
    c = Conversation(
        tenant_id=t.id,
        employee_id=e.id,
        employee_version="1.0.0",
        end_user_pseudo_id="u",
        channel="line",
        channel_user_id="U",
    )
    session.add(c)
    await session.flush()
    for i, (role, content) in enumerate(msgs, start=1):
        await session.execute(
            text(
                "INSERT INTO message (id, conversation_id, seq, role, content, created_at) "
                "VALUES (gen_random_uuid(), :cid, :s, :r, :c, NOW())"
            ),
            {"cid": str(c.id), "s": i, "r": role, "c": content},
        )
    await session.flush()
    return c.id


def test_summarize_stub_basic() -> None:
    out = _summarize_stub([("user", "請問退貨"), ("assistant", "請保留發票")])
    assert "user 首問" in out
    assert "退貨" in out
    assert "STUB 摘要" in out


def test_summarize_stub_empty_history() -> None:
    out = _summarize_stub([])
    assert "無 user 訊息" in out


async def test_generate_summary_no_messages_returns_none(
    db_session: AsyncSession,
) -> None:
    cid = uuid.uuid4()
    out = await generate_summary(db_session, conversation_id=cid)
    assert out is None


async def test_generate_summary_stub_no_llm(db_session: AsyncSession) -> None:
    cid = await _seed_conv_with_msgs(
        db_session,
        [
            ("user", "退貨期限"),
            ("assistant", "7 天內可退"),
        ],
    )
    out = await generate_summary(db_session, conversation_id=cid)
    assert out is not None
    assert "STUB" in out
    assert "退貨期限" in out


async def test_generate_summary_with_llm(db_session: AsyncSession) -> None:
    cid = await _seed_conv_with_msgs(
        db_session,
        [
            ("user", "退貨怎麼辦"),
            ("assistant", "7 天內申請"),
        ],
    )
    llm = _FakeLLM("user 問退貨流程，AI 告知 7 天內可申請。狀態：已解決。")
    out = await generate_summary(db_session, conversation_id=cid, llm_client=llm)
    assert "7 天" in out
    assert len(llm.calls) == 1


async def test_generate_summary_llm_failure_falls_back(
    db_session: AsyncSession,
) -> None:
    """LLM 噴例外 → fallback 走 stub。"""

    class _BrokenLLM(LLMClient):
        async def complete(self, **kwargs: Any) -> LLMResponse:
            raise RuntimeError("LLM down")

    cid = await _seed_conv_with_msgs(
        db_session,
        [("user", "X"), ("assistant", "Y")],
    )
    out = await generate_summary(db_session, conversation_id=cid, llm_client=_BrokenLLM())
    assert out is not None
    assert "STUB" in out


async def test_write_summary_to_conversation(db_session: AsyncSession) -> None:
    cid = await _seed_conv_with_msgs(db_session, [("user", "x"), ("assistant", "y")])
    await write_summary_to_conversation(db_session, conversation_id=cid, summary="my summary")
    row = (
        await db_session.execute(
            text("SELECT summary FROM conversation WHERE id = :cid"),
            {"cid": str(cid)},
        )
    ).scalar_one()
    assert row == "my summary"
