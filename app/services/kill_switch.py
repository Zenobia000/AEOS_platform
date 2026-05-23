"""Kill switch service — per-tenant emergency disable AI (S5 / UF-004).

對應 PRD-001 §5.5:
- ai_enabled = false → DraftProcessor 跳過 LLM 呼叫，建 conversation_handoff
- 30 秒內生效（每 turn 查 DB；單 SELECT < 1ms 可接受）
- 二次確認：disable_ai() 需傳 confirm_tenant_id（避免 admin 誤關錯客戶）
- 所有 enable / disable 進 audit_log（kill_switch.enabled / disabled）

Phase 1 簡化：
- 無 Slack 通知（待 SLACK_WEBHOOK_URL 環境設好）
- 無 in-memory cache（直接 DB；> 100 RPS 再加 30s TTL）
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.tenant_setting import TenantSetting
from app.services import audit
from app.services.notifications import notify_slack


class KillSwitchError(RuntimeError):
    """無法執行 kill switch 動作（confirm token 錯 / state 不對等）."""


@dataclass(frozen=True)
class KillSwitchState:
    tenant_id: uuid.UUID
    ai_enabled: bool
    disabled_at: datetime | None
    disabled_by: str | None
    disable_reason: str | None


async def _load_or_init(session: AsyncSession, tenant_id: uuid.UUID) -> TenantSetting:
    setting = (
        await session.execute(select(TenantSetting).where(TenantSetting.tenant_id == tenant_id))
    ).scalar_one_or_none()
    if setting is not None:
        return setting
    setting = TenantSetting(tenant_id=tenant_id, ai_enabled=True)
    session.add(setting)
    await session.flush()
    return setting


async def get_state(session: AsyncSession, tenant_id: uuid.UUID) -> KillSwitchState:
    """讀單一 tenant 的 kill switch 狀態（不存在視為 ai_enabled=True）."""
    setting = (
        await session.execute(select(TenantSetting).where(TenantSetting.tenant_id == tenant_id))
    ).scalar_one_or_none()
    if setting is None:
        return KillSwitchState(
            tenant_id=tenant_id,
            ai_enabled=True,
            disabled_at=None,
            disabled_by=None,
            disable_reason=None,
        )
    return KillSwitchState(
        tenant_id=tenant_id,
        ai_enabled=setting.ai_enabled,
        disabled_at=setting.disabled_at,
        disabled_by=setting.disabled_by,
        disable_reason=setting.disable_reason,
    )


async def is_ai_enabled(session: AsyncSession, tenant_id: uuid.UUID) -> bool:
    """Hot path：每 turn 呼叫。回傳 True 表示 AI 可運作；False 表示已被 kill。"""
    state = await get_state(session, tenant_id)
    return state.ai_enabled


async def disable_ai(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    confirm_tenant_id: uuid.UUID,
    actor_id: str,
    reason: str,
) -> KillSwitchState:
    """關閉 AI；需傳同一個 tenant_id 兩次（二次確認）.

    Raises:
        KillSwitchError: confirm_tenant_id 與 tenant_id 不一致 / reason 為空
    """
    if tenant_id != confirm_tenant_id:
        raise KillSwitchError("confirm_tenant_id mismatch — refusing for safety")
    if not reason.strip():
        raise KillSwitchError("reason cannot be empty")

    setting = await _load_or_init(session, tenant_id)
    if not setting.ai_enabled:
        raise KillSwitchError(f"AI already disabled for tenant {tenant_id}")

    setting.ai_enabled = False
    setting.disabled_at = datetime.now(UTC)
    setting.disabled_by = actor_id
    setting.disable_reason = reason[:500]
    await session.flush()

    await audit.emit(
        session,
        event_type="kill_switch.disabled",
        tenant_id=tenant_id,
        actor_id=actor_id,
        resource_type="tenant_setting",
        resource_id=str(tenant_id),
        payload={"reason": reason[:500]},
    )
    # Best-effort Slack 通知（無 webhook 設定就 skip；失敗不阻擋）
    await notify_slack(
        severity="P0",
        title="Kill switch ACTIVATED",
        message=f"AI disabled for tenant `{tenant_id}` by `{actor_id}`",
        fields={"tenant_id": str(tenant_id), "reason": reason[:200]},
    )
    return await get_state(session, tenant_id)


async def enable_ai(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: str,
    reason: str,
) -> KillSwitchState:
    """重啟 AI."""
    if not reason.strip():
        raise KillSwitchError("reason cannot be empty")

    setting = await _load_or_init(session, tenant_id)
    if setting.ai_enabled:
        raise KillSwitchError(f"AI already enabled for tenant {tenant_id}")

    setting.ai_enabled = True
    setting.disabled_at = None
    setting.disabled_by = None
    setting.disable_reason = None
    await session.flush()

    await audit.emit(
        session,
        event_type="kill_switch.enabled",
        tenant_id=tenant_id,
        actor_id=actor_id,
        resource_type="tenant_setting",
        resource_id=str(tenant_id),
        payload={"reason": reason[:500]},
    )
    await notify_slack(
        severity="info",
        title="Kill switch RESTORED",
        message=f"AI re-enabled for tenant `{tenant_id}` by `{actor_id}`",
        fields={"tenant_id": str(tenant_id), "reason": reason[:200]},
    )
    return await get_state(session, tenant_id)
