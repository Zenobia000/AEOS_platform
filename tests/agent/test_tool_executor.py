"""ToolExecutor 行為測試 — internal/function dispatch + http_api mock + invocation 紀錄."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tool_executor import (
    InternalToolRegistry,
    ToolExecutionContext,
    ToolExecutor,
    ToolNotFoundError,
)
from app.db.models.tenant import Tenant
from app.db.models.tool import Tool
from app.db.models.tool_invocation import ToolInvocation


async def _make_tenant(session: AsyncSession, slug: str) -> Tenant:
    t = Tenant(name=f"T-{slug}", slug=slug)
    session.add(t)
    await session.flush()
    return t


async def _make_internal_tool(
    session: AsyncSession,
    slug: str,
    *,
    timeout_ms: int = 5000,
    enabled: bool = True,
) -> Tool:
    t = Tool(
        tenant_id=None,
        slug=slug,
        name=slug,
        description=f"internal tool {slug}",
        tool_type="internal",
        input_schema={"type": "object"},
        timeout_ms=timeout_ms,
        enabled=enabled,
    )
    session.add(t)
    await session.flush()
    return t


def _ctx(session: AsyncSession, tenant_id: uuid.UUID) -> ToolExecutionContext:
    return ToolExecutionContext(
        tenant_id=tenant_id,
        conversation_id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        skill_version_id=uuid.uuid4(),
        session=session,
    )


# ── InternalToolRegistry ────────────────────────────


def test_registry_register_and_lookup() -> None:
    reg = InternalToolRegistry()

    async def h(args: dict[str, Any], ctx: ToolExecutionContext) -> str:
        return "ok"

    reg.register("foo", h)
    assert reg.get("foo") is h
    assert reg.get("bar") is None
    assert "foo" in reg.slugs()


def test_registry_rejects_duplicate() -> None:
    reg = InternalToolRegistry()

    async def h(args: dict[str, Any], ctx: ToolExecutionContext) -> str:
        return "ok"

    reg.register("foo", h)
    with pytest.raises(ValueError, match="already registered"):
        reg.register("foo", h)


# ── Internal dispatch ──────────────────────────────


async def test_dispatch_internal_success(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "te-internal")
    await _make_internal_tool(db_session, "echo")

    reg = InternalToolRegistry()

    async def echo(args: dict[str, Any], ctx: ToolExecutionContext) -> dict[str, Any]:
        return {"echoed": args, "tenant": str(ctx.tenant_id)}

    reg.register("echo", echo)
    executor = ToolExecutor(registry=reg)

    result = await executor.dispatch(
        "echo",
        {"x": 1},
        ctx=_ctx(db_session, tenant.id),
    )

    assert result.status == "success"
    assert result.output["echoed"] == {"x": 1}
    assert result.error_message is None
    assert result.latency_ms >= 0


async def test_dispatch_records_invocation_success(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "te-rec-ok")
    tool = await _make_internal_tool(db_session, "noop")

    reg = InternalToolRegistry()

    async def noop(args: dict[str, Any], ctx: ToolExecutionContext) -> dict[str, str]:
        return {"ok": "yes"}

    reg.register("noop", noop)
    executor = ToolExecutor(registry=reg)

    await executor.dispatch("noop", {"q": "x"}, ctx=_ctx(db_session, tenant.id))

    inv = (
        await db_session.execute(select(ToolInvocation).where(ToolInvocation.tool_id == tool.id))
    ).scalar_one()
    assert inv.status == "success"
    assert inv.input == {"q": "x"}
    assert inv.output == {"ok": "yes"}
    assert inv.error_message is None
    assert inv.latency_ms is not None and inv.latency_ms >= 0


async def test_dispatch_records_error(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "te-rec-err")
    tool = await _make_internal_tool(db_session, "explode")

    reg = InternalToolRegistry()

    async def explode(args: dict[str, Any], ctx: ToolExecutionContext) -> Any:
        raise RuntimeError("boom")

    reg.register("explode", explode)
    executor = ToolExecutor(registry=reg)
    result = await executor.dispatch(
        "explode",
        {},
        ctx=_ctx(db_session, tenant.id),
    )

    assert result.status == "error"
    assert "boom" in result.error_message  # type: ignore[operator]

    inv = (
        await db_session.execute(select(ToolInvocation).where(ToolInvocation.tool_id == tool.id))
    ).scalar_one()
    assert inv.status == "error"
    assert inv.output is None
    assert "RuntimeError" in inv.error_message  # type: ignore[operator]


async def test_dispatch_timeout(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "te-timeout")
    tool = await _make_internal_tool(db_session, "slow", timeout_ms=50)

    reg = InternalToolRegistry()

    async def slow(args: dict[str, Any], ctx: ToolExecutionContext) -> str:
        await asyncio.sleep(0.5)
        return "should not reach"

    reg.register("slow", slow)
    executor = ToolExecutor(registry=reg)
    result = await executor.dispatch("slow", {}, ctx=_ctx(db_session, tenant.id))

    assert result.status == "timeout"
    assert "timeout_ms=50" in result.error_message  # type: ignore[operator]

    inv = (
        await db_session.execute(select(ToolInvocation).where(ToolInvocation.tool_id == tool.id))
    ).scalar_one()
    assert inv.status == "timeout"


async def test_dispatch_unknown_tool_raises(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "te-unknown")
    executor = ToolExecutor()
    with pytest.raises(ToolNotFoundError):
        await executor.dispatch("nope", {}, ctx=_ctx(db_session, tenant.id))


async def test_dispatch_disabled_tool_raises(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "te-disabled")
    await _make_internal_tool(db_session, "off", enabled=False)
    executor = ToolExecutor()
    with pytest.raises(ToolNotFoundError):
        await executor.dispatch("off", {}, ctx=_ctx(db_session, tenant.id))


async def test_dispatch_internal_no_handler_raises(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "te-no-handler")
    await _make_internal_tool(db_session, "ghost")
    executor = ToolExecutor()  # empty registry
    result = await executor.dispatch("ghost", {}, ctx=_ctx(db_session, tenant.id))
    assert result.status == "error"
    assert "no internal handler" in result.error_message  # type: ignore[operator]


# ── HTTP dispatch（mock httpx）────────────────────


async def _make_http_tool(
    session: AsyncSession,
    slug: str = "remote",
    *,
    auth_method: str | None = "api_key",
) -> Tool:
    t = Tool(
        tenant_id=None,
        slug=slug,
        name=slug,
        description="remote api",
        tool_type="http_api",
        endpoint="https://api.example.com/v1/x",
        auth_method=auth_method,
        auth_config={"key": "sk-test", "header": "x-api-key"} if auth_method == "api_key" else None,
        input_schema={"type": "object"},
    )
    session.add(t)
    await session.flush()
    return t


async def test_dispatch_http_api_success(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "te-http")
    await _make_http_tool(db_session, "remote_search")

    captured: dict[str, Any] = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = request.read().decode()
        captured["headers"] = dict(request.headers)
        return httpx.Response(200, json={"hits": [{"id": "abc"}]})

    transport = httpx.MockTransport(_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        executor = ToolExecutor(http_client=client)
        result = await executor.dispatch(
            "remote_search",
            {"q": "退貨"},
            ctx=_ctx(db_session, tenant.id),
        )

    assert result.status == "success"
    assert result.output == {"hits": [{"id": "abc"}]}
    assert captured["url"] == "https://api.example.com/v1/x"
    assert '"q":"退貨"' in captured["body"] or '"q": "退貨"' in captured["body"]
    assert captured["headers"]["x-api-key"] == "sk-test"


async def test_dispatch_http_5xx_records_error(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "te-http-err")
    tool = await _make_http_tool(db_session, "broken", auth_method=None)

    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    transport = httpx.MockTransport(_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        executor = ToolExecutor(http_client=client)
        result = await executor.dispatch(
            "broken",
            {},
            ctx=_ctx(db_session, tenant.id),
        )

    assert result.status == "error"
    assert "500" in result.error_message  # type: ignore[operator]
    inv = (
        await db_session.execute(select(ToolInvocation).where(ToolInvocation.tool_id == tool.id))
    ).scalar_one()
    assert inv.status == "error"


async def test_dispatch_http_no_client_errors(db_session: AsyncSession) -> None:
    """http_api tool 但 ToolExecutor 沒注入 http_client → error 記錄."""
    tenant = await _make_tenant(db_session, "te-http-noclient")
    await _make_http_tool(db_session, "remote2", auth_method=None)
    executor = ToolExecutor()  # 沒 http_client
    result = await executor.dispatch("remote2", {}, ctx=_ctx(db_session, tenant.id))
    assert result.status == "error"
    assert "http_client" in result.error_message  # type: ignore[operator]


# ── db_query tool_type Phase 2 placeholder ─────────


async def test_dispatch_db_query_not_implemented(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "te-db-query")
    t = Tool(
        tenant_id=None,
        slug="some_query",
        name="x",
        description="x",
        tool_type="db_query",
        input_schema={"type": "object"},
    )
    db_session.add(t)
    await db_session.flush()

    executor = ToolExecutor()
    result = await executor.dispatch("some_query", {}, ctx=_ctx(db_session, tenant.id))
    assert result.status == "error"
    assert "Phase 2" in result.error_message  # type: ignore[operator]


# ── record_invocations=False（測試模式）────────────


async def test_dispatch_skip_record_when_disabled(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "te-skip-rec")
    tool = await _make_internal_tool(db_session, "no_record")

    reg = InternalToolRegistry()

    async def h(args: dict[str, Any], ctx: ToolExecutionContext) -> str:
        return "ok"

    reg.register("no_record", h)
    executor = ToolExecutor(registry=reg, record_invocations=False)
    await executor.dispatch("no_record", {}, ctx=_ctx(db_session, tenant.id))

    invs = (
        (await db_session.execute(select(ToolInvocation).where(ToolInvocation.tool_id == tool.id)))
        .scalars()
        .all()
    )
    assert invs == []
