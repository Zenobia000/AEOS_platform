"""LINE Messaging Platform webhook endpoint.

依 API-002 + MC-011 + SEC-001 §6.1 #1:
- POST /api/v1/webhooks/line/{channel_id}
- HMAC-SHA256 簽章驗證（X-Line-Signature header）
- Webhook event 去重（webhook_event 表複合 PK (id, channel)）
- ≤ 1s ACK（依 NFR-001 §1）
- 簽章失敗 → 403 + audit log (SEC-001 §6.1 #1 ai.webhook_signature_failed)

Phase 1 簡化：
- channel_secret 從 channel_binding.config['channel_secret'] 讀；prod 應走
  Secret Manager（auth_config encrypted at rest）
- 訊息存進 message 表後不在 webhook 內跑 LLM —— 由 worker pull 或 enqueue
  (Phase 1 stub：直接 return 200，後續 enqueue worker 在 Tier 4 後續)
- Reply Token Phase 1 不用（依 ADR-0011 用 Push API；ADR-0001/MC-011）
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Path, Request, status
from sqlalchemy import select

from app.db.models.channel_binding import ChannelBinding
from app.db.models.conversation import Conversation
from app.db.models.employee import Employee
from app.db.session import session_scope
from app.services import audit

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhook"])

CHANNEL = "line"


def verify_line_signature(body: bytes, signature: str, channel_secret: str) -> bool:
    """LINE HMAC-SHA256 簽章驗證（依 LINE Developers 規範）.

    LINE 把 channel_secret 作 key，request body 作 message，產 base64 SHA256。
    """
    if not signature or not channel_secret:
        return False
    digest = hmac.new(
        channel_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected, signature)


@router.post(
    "/line/{channel_id}",
    summary="LINE Messaging webhook",
    description=(
        "驗 HMAC-SHA256 → dedup via webhook_event PK → 寫 message 進 DB。"
        "目標 p95 ≤ 1s ACK (NFR-001 §1)。"
    ),
)
async def line_webhook(
    request: Request,
    channel_id: str = Path(..., description="LINE OA channel id"),
    x_line_signature: str | None = Header(default=None, alias="X-Line-Signature"),
) -> dict[str, Any]:
    body = await request.body()

    async with session_scope() as session:
        # 1. 找 channel_binding（依 config.channel_id 比對）
        binding = await _find_binding(session, channel_id)
        if binding is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"channel_binding not found for line channel_id={channel_id}",
            )
        if not binding.enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="channel_binding disabled",
            )

        channel_secret = str(binding.config.get("channel_secret", ""))

        # 2. HMAC-SHA256 簽章驗證
        if not verify_line_signature(body, x_line_signature or "", channel_secret):
            await _audit_signature_fail(session, binding, channel_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="invalid X-Line-Signature",
            )

        # 3. 解析 payload
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"invalid json: {exc}",
            ) from exc

        events = payload.get("events", [])
        if not isinstance(events, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="events must be a list",
            )

        # 4. 找 employee → tenant
        employee = (
            await session.execute(select(Employee).where(Employee.id == binding.employee_id))
        ).scalar_one()
        tenant_id = employee.tenant_id

        processed = 0
        deduped = 0
        accepted_events: list[dict[str, Any]] = []

        for ev in events:
            if not isinstance(ev, dict):
                continue
            event_id = str(ev.get("webhookEventId", ""))
            if not event_id:
                continue

            # 5. dedup via webhook_event PK
            if await _is_duplicate(session, event_id):
                deduped += 1
                continue

            # 6. 處理 message event（其他事件 Phase 2）
            if ev.get("type") == "message" and isinstance(ev.get("message"), dict):
                await _record_inbound_message(
                    session,
                    tenant_id=tenant_id,
                    employee=employee,
                    event=ev,
                )
                accepted_events.append({"event_id": event_id, "type": "message"})
                processed += 1
            else:
                accepted_events.append(
                    {
                        "event_id": event_id,
                        "type": str(ev.get("type", "unknown")),
                        "status": "skipped",
                    }
                )

        await audit.emit(
            session,
            event_type="channel.webhook_received",
            tenant_id=tenant_id,
            actor_id=f"line:{channel_id}",
            resource_type="webhook",
            resource_id=channel_id,
            payload={
                "events_total": len(events),
                "processed": processed,
                "deduped": deduped,
            },
        )

        return {
            "status": "ok",
            "processed": processed,
            "deduped": deduped,
            "events": accepted_events,
        }


# ── helpers ──────────────────────────────────────────


async def _find_binding(session: Any, channel_id: str) -> ChannelBinding | None:
    """channel_binding.config->>'channel_id' = :cid 比對."""
    result = await session.execute(
        select(ChannelBinding).where(
            ChannelBinding.channel == CHANNEL,
            ChannelBinding.config["channel_id"].astext == channel_id,
        )
    )
    binding: ChannelBinding | None = result.scalar_one_or_none()
    return binding


async def _is_duplicate(session: Any, event_id: str) -> bool:
    """ON CONFLICT DO NOTHING — 不會破壞 transaction."""
    from sqlalchemy import text

    result = await session.execute(
        text(
            "INSERT INTO webhook_event (id, channel) "
            "VALUES (:eid, :ch) "
            "ON CONFLICT (id, channel) DO NOTHING "
            "RETURNING id"
        ),
        {"eid": event_id, "ch": CHANNEL},
    )
    return result.first() is None  # None = conflict → duplicate


async def _record_inbound_message(
    session: Any,
    *,
    tenant_id: uuid.UUID,
    employee: Employee,
    event: dict[str, Any],
) -> None:
    """寫 inbound message 進 conversation/message。

    Phase 1 簡化：每個 LINE user 單一持續對話（依 channel_user_id 找 active）；
    若無 active conversation 新建一個。
    """
    from sqlalchemy import text

    source = event.get("source", {})
    line_user_id = str(source.get("userId", ""))
    message = event.get("message", {})
    content = str(message.get("text", ""))

    # pseudonymize: 用 sha256 取代真 line_user_id（依 ADR-0005）
    pseudo = hashlib.sha256(line_user_id.encode("utf-8")).hexdigest()[:32]

    # 找 active conversation（status in open/active/waiting_human）
    conv = (
        await session.execute(
            select(Conversation).where(
                Conversation.tenant_id == tenant_id,
                Conversation.employee_id == employee.id,
                Conversation.channel == CHANNEL,
                Conversation.channel_user_id == line_user_id,
                Conversation.status.in_(["open", "active", "waiting_human"]),
            )
        )
    ).scalar_one_or_none()

    if conv is None:
        conv = Conversation(
            tenant_id=tenant_id,
            employee_id=employee.id,
            employee_version=employee.version,
            end_user_pseudo_id=pseudo,
            channel=CHANNEL,
            channel_user_id=line_user_id,
        )
        session.add(conv)
        await session.flush()

    # 直接 raw INSERT 進 message partition (Message ORM 對 partition 有時麻煩)
    next_seq = (conv.message_count or 0) + 1
    await session.execute(
        text(
            "INSERT INTO message (id, conversation_id, seq, role, content, created_at) "
            "VALUES (gen_random_uuid(), :cid, :seq, 'user', :content, NOW())"
        ),
        {"cid": str(conv.id), "seq": next_seq, "content": content},
    )

    # 更新 conversation counter + last_message_at
    await session.execute(
        text(
            "UPDATE conversation "
            "SET message_count = message_count + 1, "
            "    last_message_at = NOW(), "
            "    status = CASE WHEN status='open' THEN 'active' ELSE status END "
            "WHERE id = :cid"
        ),
        {"cid": str(conv.id)},
    )


async def _audit_signature_fail(
    session: Any,
    binding: ChannelBinding,
    channel_id: str,
) -> None:
    """簽章驗證失敗發 audit (SEC-001 §6.1 #1)."""
    employee = (
        await session.execute(select(Employee).where(Employee.id == binding.employee_id))
    ).scalar_one()
    await audit.emit(
        session,
        event_type="channel.webhook_signature_failed",
        tenant_id=employee.tenant_id,
        actor_id=f"line:{channel_id}",
        resource_type="webhook",
        resource_id=channel_id,
        payload={"channel": CHANNEL},
    )
