"""AuditHook 行為測試 — 需 DB（驗證 audit_log row 寫入）."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.context import AgentContext
from app.agent.hooks.audit import AuditHook
from app.db.models.audit_log import AuditLog
from app.llm.client import LLMResponse, LLMUsage


def _ctx(session: AsyncSession) -> AgentContext:
    return AgentContext(
        tenant_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        employee_version="1.0.0",
        skill_version_id=uuid.uuid4(),
        session=session,
    )


async def test_audit_hook_writes_llm_call(db_session: AsyncSession) -> None:
    hook = AuditHook()
    ctx = _ctx(db_session)
    resp = LLMResponse(
        text="ok",
        model="claude-sonnet-4-6",
        stop_reason="end_turn",
        usage=LLMUsage(input_tokens=100, output_tokens=50),
    )

    await hook.after_llm_call(ctx, resp)
    await db_session.flush()

    rows = (
        (await db_session.execute(select(AuditLog).where(AuditLog.event_type == "ai.llm_call")))
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].tenant_id == ctx.tenant_id
    assert rows[0].payload["model"] == "claude-sonnet-4-6"
    assert rows[0].payload["input_tokens"] == 100
    assert rows[0].payload["output_tokens"] == 50


async def test_audit_hook_writes_tool_call_success(db_session: AsyncSession) -> None:
    hook = AuditHook()
    ctx = _ctx(db_session)

    await hook.after_tool_call(
        ctx,
        tool_name="search_knowledge",
        tool_input={"q": "退貨"},
        tool_output={"results": []},
        error=None,
    )
    await db_session.flush()

    row = (
        await db_session.execute(select(AuditLog).where(AuditLog.event_type == "ai.tool_call"))
    ).scalar_one()
    assert row.resource_id == "search_knowledge"
    assert row.payload["status"] == "success"
    assert row.payload["error_message"] is None


async def test_audit_hook_writes_tool_call_error(db_session: AsyncSession) -> None:
    hook = AuditHook()
    ctx = _ctx(db_session)

    await hook.after_tool_call(
        ctx,
        tool_name="search_knowledge",
        tool_input={"q": "x"},
        tool_output=None,
        error=ValueError("API down"),
    )
    await db_session.flush()

    row = (
        await db_session.execute(select(AuditLog).where(AuditLog.event_type == "ai.tool_call"))
    ).scalar_one()
    assert row.payload["status"] == "error"
    assert "API down" in row.payload["error_message"]


async def test_audit_hook_skips_when_no_session() -> None:
    """ctx.session=None 時，hook 應靜默 no-op（不 raise）."""
    hook = AuditHook()
    ctx = AgentContext(
        tenant_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        employee_version="1.0.0",
        skill_version_id=None,
        session=None,
    )
    resp = LLMResponse(usage=LLMUsage(input_tokens=0, output_tokens=0))

    # 不該 raise
    await hook.after_llm_call(ctx, resp)
    await hook.after_tool_call(ctx, "x", {}, None)


async def test_audit_payload_includes_skill_version(db_session: AsyncSession) -> None:
    hook = AuditHook()
    ctx = _ctx(db_session)
    resp = LLMResponse(usage=LLMUsage(input_tokens=10, output_tokens=5))

    await hook.after_llm_call(ctx, resp)
    await db_session.flush()

    row = (
        await db_session.execute(select(AuditLog).where(AuditLog.event_type == "ai.llm_call"))
    ).scalar_one()
    assert row.payload["skill_version_id"] == str(ctx.skill_version_id)
