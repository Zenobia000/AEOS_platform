"""Canary routing service — per-tenant Draft Mode → auto-reply 漸進放鬆 (S5).

對應 S5 §Canary：
- 0 = 全 Draft Mode（保守，pilot 上線初始）
- 25 / 50 / 75 / 100 = 漸進放鬆比例（auto-reply 直送）
- bucket 決定基於 conversation.id hash 取模（確定性；同 conversation 永遠
  同 bucket，避免 UX 跳動）

API:
- get_canary_percent(session, tenant_id) -> int
- set_canary_percent(session, tenant_id, percent, actor_id, reason) -> result
- decide_outbound_status(conversation_id, canary_percent) -> 'pending' | 'awaiting_review'
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.tenant_setting import TenantSetting
from app.services import audit


class CanaryError(RuntimeError):
    """Canary 操作無法執行（percent 不合法 / 沒變等）."""


@dataclass(frozen=True)
class CanaryState:
    tenant_id: uuid.UUID
    canary_percent: int


def _bucket_for_conversation(conversation_id: uuid.UUID) -> int:
    """conversation.id → 0~99 bucket（確定性）.

    用 SHA256(uuid_bytes) 取前 4 bytes → int → mod 100。
    比 UUID.int 直接 mod 更均勻（UUID 結構有版本/變體位元，分布不均）。
    """
    digest = hashlib.sha256(conversation_id.bytes).digest()[:4]
    return int.from_bytes(digest, "big") % 100


def decide_outbound_status(
    *,
    conversation_id: uuid.UUID,
    canary_percent: int,
) -> Literal["pending", "awaiting_review"]:
    """根據 canary_percent + conversation hash 決定 outbound 初始 status."""
    if canary_percent <= 0:
        return "awaiting_review"
    if canary_percent >= 100:
        return "pending"
    return (
        "pending"
        if _bucket_for_conversation(conversation_id) < canary_percent
        else "awaiting_review"
    )


async def _load_or_init(session: AsyncSession, tenant_id: uuid.UUID) -> TenantSetting:
    setting = (
        await session.execute(select(TenantSetting).where(TenantSetting.tenant_id == tenant_id))
    ).scalar_one_or_none()
    if setting is not None:
        return setting
    setting = TenantSetting(tenant_id=tenant_id)
    session.add(setting)
    await session.flush()
    return setting


async def get_canary_percent(session: AsyncSession, *, tenant_id: uuid.UUID) -> int:
    """讀單一 tenant canary_percent；不存在視為 0（全 Draft Mode）."""
    setting = (
        await session.execute(select(TenantSetting).where(TenantSetting.tenant_id == tenant_id))
    ).scalar_one_or_none()
    if setting is None:
        return 0
    return setting.canary_percent


async def set_canary_percent(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    percent: int,
    actor_id: str,
    reason: str,
) -> CanaryState:
    """設 canary_percent；audit canary.percent_changed.

    Raises:
        CanaryError: percent 不在 0~100 / reason 為空 / 無變化
    """
    if percent < 0 or percent > 100:
        raise CanaryError(f"canary_percent must be 0-100; got {percent}")
    if not reason.strip():
        raise CanaryError("reason cannot be empty")

    setting = await _load_or_init(session, tenant_id)
    if setting.canary_percent == percent:
        raise CanaryError(f"canary_percent already {percent}; no change")

    old = setting.canary_percent
    setting.canary_percent = percent
    setting.updated_at = datetime.now(UTC)
    await session.flush()

    await audit.emit(
        session,
        event_type="canary.percent_changed",
        tenant_id=tenant_id,
        actor_id=actor_id,
        resource_type="tenant_setting",
        resource_id=str(tenant_id),
        payload={"old_percent": old, "new_percent": percent, "reason": reason[:500]},
    )

    return CanaryState(tenant_id=tenant_id, canary_percent=percent)
