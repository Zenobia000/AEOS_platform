"""ToolExecutor — 依 MC-006 tool_type 分派 tool call 執行.

設計（Phase 1 簡化）：
- 從 DB tool 表查 tool_type / endpoint / auth / timeout / retry_policy
- 依 tool_type 路由：
  * 'internal' / 'function' → 註冊在 InternalRegistry 的 Python async callable
  * 'http_api' → 用 httpx async 呼叫 endpoint
  * 'db_query' → Phase 2（本檔 raise NotImplementedError）
- 寫入 tool_invocation 表（status / input / output / latency_ms / error）
- output PII-masking 由 caller 在 input 傳入前完成（本層不處理）

與 EmployeeRuntime 的關係：本 class 是 `ToolExecutor` callable 的具體實作；
EmployeeRuntime 構造時 `tool_executor=db_backed_executor.dispatch` 即可。
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.tool import Tool
from app.db.models.tool_invocation import ToolInvocation

InternalHandler = Callable[[dict[str, Any], "ToolExecutionContext"], Awaitable[Any]]


class ToolNotFoundError(RuntimeError):
    """tool slug 不存在於 DB tool 表."""


class ToolTimeoutError(RuntimeError):
    """tool call 超過 timeout_ms."""


@dataclass(frozen=True)
class ToolExecutionContext:
    """傳給 internal handler 的 context（最小集；之後依需要擴）."""

    tenant_id: uuid.UUID
    conversation_id: uuid.UUID | None
    employee_id: uuid.UUID | None
    skill_version_id: uuid.UUID | None
    session: AsyncSession


@dataclass(frozen=True)
class ToolExecutionResult:
    """ToolExecutor.dispatch() 回傳值."""

    output: Any
    latency_ms: int
    status: str  # success / error / timeout
    error_message: str | None = None


class InternalToolRegistry:
    """Phase 1 註冊 internal/function tool 的 callable."""

    def __init__(self) -> None:
        self._handlers: dict[str, InternalHandler] = {}

    def register(self, slug: str, handler: InternalHandler) -> None:
        if slug in self._handlers:
            raise ValueError(f"tool handler already registered: {slug}")
        self._handlers[slug] = handler

    def get(self, slug: str) -> InternalHandler | None:
        return self._handlers.get(slug)

    def slugs(self) -> tuple[str, ...]:
        return tuple(self._handlers.keys())


class ToolExecutor:
    """DB-backed tool executor — 依 MC-006 分派 + 寫 tool_invocation 紀錄.

    Args:
        registry: InternalToolRegistry — 'internal' / 'function' tool 用
        http_client: 注入用 httpx.AsyncClient（測試方便；prod 由 caller 管 lifecycle）
        record_invocations: True 寫 tool_invocation row；False（測試）跳過
    """

    def __init__(
        self,
        *,
        registry: InternalToolRegistry | None = None,
        http_client: httpx.AsyncClient | None = None,
        record_invocations: bool = True,
    ) -> None:
        self._registry = registry or InternalToolRegistry()
        self._http_client = http_client
        self._record = record_invocations

    @property
    def registry(self) -> InternalToolRegistry:
        return self._registry

    async def dispatch(
        self,
        slug: str,
        tool_input: dict[str, Any],
        *,
        ctx: ToolExecutionContext,
    ) -> ToolExecutionResult:
        """主入口：依 DB tool.tool_type 分派 + 記錄 invocation."""
        tool = await self._load_tool(ctx.session, slug)

        start = time.perf_counter()
        output: Any = None
        status = "success"
        error_message: str | None = None

        try:
            output = await self._invoke(tool, tool_input, ctx)
        except TimeoutError:
            status = "timeout"
            error_message = f"tool {slug} exceeded timeout_ms={tool.timeout_ms}"
        except Exception as exc:
            status = "error"
            error_message = f"{type(exc).__name__}: {exc}"

        latency_ms = int((time.perf_counter() - start) * 1000)

        if self._record:
            await self._record_invocation(
                ctx,
                tool=tool,
                tool_input=tool_input,
                output=output if status == "success" else None,
                status=status,
                error_message=error_message,
                latency_ms=latency_ms,
            )

        return ToolExecutionResult(
            output=output if status == "success" else None,
            latency_ms=latency_ms,
            status=status,
            error_message=error_message,
        )

    # ── private helpers ──────────────────────────────

    async def _load_tool(self, session: AsyncSession, slug: str) -> Tool:
        row = (await session.execute(select(Tool).where(Tool.slug == slug))).scalar_one_or_none()
        if row is None:
            raise ToolNotFoundError(f"tool not registered in DB: {slug}")
        if not row.enabled:
            raise ToolNotFoundError(f"tool disabled: {slug}")
        return row

    async def _invoke(
        self,
        tool: Tool,
        tool_input: dict[str, Any],
        ctx: ToolExecutionContext,
    ) -> Any:
        timeout_s = tool.timeout_ms / 1000

        if tool.tool_type in ("internal", "function"):
            return await self._invoke_internal(tool, tool_input, ctx, timeout_s)
        if tool.tool_type == "http_api":
            return await self._invoke_http(tool, tool_input, timeout_s)
        if tool.tool_type == "db_query":
            raise NotImplementedError("db_query tool_type is Phase 2 (MC-006 §future)")
        raise RuntimeError(f"unsupported tool_type: {tool.tool_type}")

    async def _invoke_internal(
        self,
        tool: Tool,
        tool_input: dict[str, Any],
        ctx: ToolExecutionContext,
        timeout_s: float,
    ) -> Any:
        handler = self._registry.get(tool.slug)
        if handler is None:
            raise ToolNotFoundError(f"no internal handler registered for tool: {tool.slug}")
        try:
            return await asyncio.wait_for(handler(tool_input, ctx), timeout=timeout_s)
        except TimeoutError:
            raise
        except asyncio.TimeoutError as exc:  # noqa: UP041 - asyncio < 3.11 alias
            raise TimeoutError(str(exc)) from exc

    async def _invoke_http(
        self,
        tool: Tool,
        tool_input: dict[str, Any],
        timeout_s: float,
    ) -> Any:
        if tool.endpoint is None:
            raise RuntimeError(f"http_api tool {tool.slug} missing endpoint")
        if self._http_client is None:
            raise RuntimeError(f"ToolExecutor needs http_client for http_api tool {tool.slug}")

        headers = _build_auth_headers(tool)
        try:
            resp = await self._http_client.post(
                tool.endpoint,
                json=tool_input,
                headers=headers,
                timeout=timeout_s,
            )
        except httpx.TimeoutException as exc:
            raise TimeoutError(f"HTTP timeout: {exc}") from exc
        resp.raise_for_status()
        return resp.json()

    async def _record_invocation(
        self,
        ctx: ToolExecutionContext,
        *,
        tool: Tool,
        tool_input: dict[str, Any],
        output: Any,
        status: str,
        error_message: str | None,
        latency_ms: int,
    ) -> None:
        # JSON-serialize 後再存（避免奇怪型別）
        inv = ToolInvocation(
            tenant_id=ctx.tenant_id,
            conversation_id=ctx.conversation_id,
            message_id=None,
            tool_id=tool.id,
            employee_id=ctx.employee_id,
            skill_version_id=ctx.skill_version_id,
            input=tool_input,
            output=output,
            status=status,
            error_message=error_message,
            latency_ms=latency_ms,
        )
        ctx.session.add(inv)
        await ctx.session.flush()


def _build_auth_headers(tool: Tool) -> dict[str, str]:
    """依 tool.auth_method 組 HTTP headers.

    Phase 1：auth_config 假定為明文（之後接 Secret Manager / encrypted at-rest）。
    """
    headers: dict[str, str] = {"content-type": "application/json"}
    if tool.auth_method is None or tool.auth_method == "none":
        return headers
    config = tool.auth_config or {}
    if tool.auth_method == "api_key":
        key = str(config.get("key", ""))
        header_name = str(config.get("header", "x-api-key"))
        headers[header_name] = key
    elif tool.auth_method == "bearer":
        headers["authorization"] = f"Bearer {config.get('token', '')}"
    elif tool.auth_method == "basic":
        import base64

        creds = f"{config.get('username', '')}:{config.get('password', '')}"
        encoded = base64.b64encode(creds.encode()).decode()
        headers["authorization"] = f"Basic {encoded}"
    elif tool.auth_method == "hmac":
        # HMAC 簽章在 prod 通常要簽 request body，Phase 1 簡化為加 secret header
        headers["x-hmac-secret-ref"] = str(config.get("secret_ref", ""))
    return headers
