"""OutboundProcessor — 把 pending outbound_message 推到 LINE Push API.

對應 MC-011 + API-002 + PRD-001 §5.5 F-CAN-01 (push outbound)：
- 撿 status IN ('pending','retrying') 的 outbound_message
- 從 channel_binding.config 取 LINE channel_access_token
- 從 message 表取 content (message_id 邏輯指向)
- POST https://api.line.me/v2/bot/message/push
- 依結果更新 status:
  * 200 → sent + sent_at = NOW()
  * 429 → retrying + retry_count++ (rate-limit；caller 排程下次)
  * 5xx → retrying + retry_count++ (exp backoff caller 排)
  * 4xx (非 429) → failed (永久錯誤；不重試)
  * 超過 max_retries (預設 3) → failed
- 寫 audit channel.message_pushed / channel.message_push_failed

Phase 1 簡化：
- 本 class 純粹處理「單筆 outbound」邏輯；polling / 排程 / backoff 計算
  由外層 worker loop 控制（Phase 1 可用 asyncio.create_task；Phase 2 接 Redis queue）
- 不做 LINE Reply Token（依 ADR/MC-011 用 Push 而非 Reply）
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.channel_binding import ChannelBinding
from app.db.models.conversation import Conversation
from app.db.models.outbound_message import OutboundMessage
from app.observability import outbound_failed_total, outbound_sent_total
from app.services import audit
from app.services.notifications import notify_slack

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
DEFAULT_MAX_RETRIES = 3


@dataclass(frozen=True)
class PushResult:
    """OutboundProcessor.process_one() 回傳值."""

    outbound_id: uuid.UUID
    status: str  # sent / retrying / failed
    http_status: int | None
    error: str | None = None


class OutboundProcessor:
    """LINE Push outbound 處理器（單筆執行；polling 由外層）.

    Args:
        http_client: 注入用 httpx.AsyncClient（測試用 MockTransport）
        max_retries: 超過即標 failed（Phase 1 預設 3）
    """

    def __init__(
        self,
        *,
        http_client: httpx.AsyncClient,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self._http = http_client
        self._max_retries = max_retries

    async def process_one(
        self,
        session: AsyncSession,
        outbound: OutboundMessage,
    ) -> PushResult:
        """Push 單一 outbound_message → LINE.

        前置條件：caller 已 lock / claim 該 row（避免並發處理）；本 Phase 1
        簡化版不做 SELECT FOR UPDATE。
        """
        if outbound.channel != "line":
            return await self._fail_permanent(
                session,
                outbound,
                error=f"unsupported channel: {outbound.channel}",
                http_status=None,
            )

        # 取 content + channel_access_token
        content = await _load_message_content(session, outbound.message_id)
        if content is None:
            return await self._fail_permanent(
                session,
                outbound,
                error=f"message {outbound.message_id} not found",
                http_status=None,
            )

        token = await _load_channel_token(session, outbound.conversation_id)
        if token is None:
            return await self._fail_permanent(
                session,
                outbound,
                error="channel_access_token not found in channel_binding",
                http_status=None,
            )

        # Push
        try:
            resp = await self._http.post(
                LINE_PUSH_URL,
                json={
                    "to": outbound.channel_user_id,
                    "messages": [{"type": "text", "text": content}],
                },
                headers={
                    "authorization": f"Bearer {token}",
                    "content-type": "application/json",
                },
                timeout=10.0,
            )
        except httpx.TimeoutException as exc:
            return await self._retry_or_fail(
                session,
                outbound,
                error=f"timeout: {exc}",
                http_status=None,
            )
        except httpx.HTTPError as exc:
            return await self._retry_or_fail(
                session,
                outbound,
                error=f"http error: {exc}",
                http_status=None,
            )

        if resp.status_code == 200:
            return await self._succeed(session, outbound)
        if resp.status_code == 429 or resp.status_code >= 500:
            # transient → retry
            return await self._retry_or_fail(
                session,
                outbound,
                error=f"transient HTTP {resp.status_code}: {resp.text[:200]}",
                http_status=resp.status_code,
            )
        # 4xx (非 429) → permanent failure
        return await self._fail_permanent(
            session,
            outbound,
            error=f"HTTP {resp.status_code}: {resp.text[:200]}",
            http_status=resp.status_code,
        )

    # ── status transitions ─────────────────────────────

    async def _succeed(
        self,
        session: AsyncSession,
        outbound: OutboundMessage,
    ) -> PushResult:
        outbound.status = "sent"
        outbound.error_message = None
        # NOW() 用 func.now() 推進 DB；同時讓 ORM 看到
        from datetime import UTC, datetime

        outbound.sent_at = datetime.now(UTC)
        await session.flush()
        outbound_sent_total.labels(channel=outbound.channel).inc()
        await audit.emit(
            session,
            event_type="channel.message_pushed",
            tenant_id=outbound.tenant_id,
            actor_id="outbound_worker",
            resource_type="outbound_message",
            resource_id=str(outbound.id),
            payload={
                "channel": outbound.channel,
                "retry_count": outbound.retry_count,
            },
        )
        return PushResult(
            outbound_id=outbound.id,
            status="sent",
            http_status=200,
        )

    async def _retry_or_fail(
        self,
        session: AsyncSession,
        outbound: OutboundMessage,
        *,
        error: str,
        http_status: int | None,
    ) -> PushResult:
        new_count = outbound.retry_count + 1
        if new_count >= self._max_retries:
            return await self._fail_permanent(
                session,
                outbound,
                error=f"max_retries exceeded ({self._max_retries}); last error: {error}",
                http_status=http_status,
                retry_count=new_count,
            )

        outbound.status = "retrying"
        outbound.retry_count = new_count
        outbound.error_message = error[:500]
        await session.flush()
        return PushResult(
            outbound_id=outbound.id,
            status="retrying",
            http_status=http_status,
            error=error,
        )

    async def _fail_permanent(
        self,
        session: AsyncSession,
        outbound: OutboundMessage,
        *,
        error: str,
        http_status: int | None,
        retry_count: int | None = None,
    ) -> PushResult:
        rc = retry_count if retry_count is not None else outbound.retry_count
        outbound.status = "failed"
        outbound.retry_count = rc
        outbound.error_message = error[:500]
        await session.flush()
        outbound_failed_total.labels(channel=outbound.channel).inc()
        await audit.emit(
            session,
            event_type="channel.message_push_failed",
            tenant_id=outbound.tenant_id,
            actor_id="outbound_worker",
            resource_type="outbound_message",
            resource_id=str(outbound.id),
            payload={
                "channel": outbound.channel,
                "retry_count": rc,
                "http_status": http_status,
                "error_excerpt": error[:200],
            },
        )
        # P1 incident — outbound 永久失敗（DLQ 累積前兆）；best-effort 通知
        await notify_slack(
            severity="P1",
            title="Outbound push failed permanently",
            message=f"Channel `{outbound.channel}` push to outbound `{outbound.id}` failed after {rc} retries",
            fields={
                "tenant_id": str(outbound.tenant_id),
                "channel": outbound.channel,
                "http_status": http_status,
                "error": error[:120],
            },
        )
        return PushResult(
            outbound_id=outbound.id,
            status="failed",
            http_status=http_status,
            error=error,
        )


# ── module-level helpers ────────────────────────────


async def _load_message_content(
    session: AsyncSession,
    message_id: uuid.UUID,
) -> str | None:
    """從 message 表查 content（用 id 即可；複合 PK 但 id 來自 gen_random_uuid()）."""
    row = (
        await session.execute(
            text("SELECT content FROM message WHERE id = :mid LIMIT 1"),
            {"mid": str(message_id)},
        )
    ).first()
    if row is None:
        return None
    return str(row[0])


async def _load_channel_token(
    session: AsyncSession,
    conversation_id: uuid.UUID,
) -> str | None:
    """從 channel_binding.config['channel_access_token'] 取 token."""
    row = (
        await session.execute(
            select(ChannelBinding)
            .join(Conversation, Conversation.employee_id == ChannelBinding.employee_id)
            .where(
                Conversation.id == conversation_id,
                ChannelBinding.channel == "line",
                ChannelBinding.enabled.is_(True),
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    token = row.config.get("channel_access_token")
    if not token:
        return None
    return str(token)
