"""Admin API — kill switch + 未來的 canary toggle (S5).

Phase 1：無 auth；S5 接 MFA + RBAC 後改 server-side。
- GET  /api/v1/admin/kill-switch/{tenant_id}    — 查狀態
- POST /api/v1/admin/kill-switch/{tenant_id}/disable
- POST /api/v1/admin/kill-switch/{tenant_id}/enable
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.auth_dependency import current_expert
from app.db.session import session_scope
from app.services import kill_switch

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(current_expert)],
)


class DisableRequest(BaseModel):
    confirm_tenant_id: uuid.UUID = Field(
        ..., description="二次確認 — 必須與 path 的 tenant_id 完全一致"
    )
    actor_id: str = Field(min_length=1, max_length=255)
    reason: str = Field(min_length=1, max_length=500)


class EnableRequest(BaseModel):
    actor_id: str = Field(min_length=1, max_length=255)
    reason: str = Field(min_length=1, max_length=500)


def _state_to_json(state: kill_switch.KillSwitchState) -> dict[str, object]:
    return {
        "tenant_id": str(state.tenant_id),
        "ai_enabled": state.ai_enabled,
        "disabled_at": state.disabled_at.isoformat() if state.disabled_at else None,
        "disabled_by": state.disabled_by,
        "disable_reason": state.disable_reason,
    }


@router.get(
    "/kill-switch/{tenant_id}",
    summary="Get kill switch state for tenant",
)
async def get_kill_switch(tenant_id: uuid.UUID) -> dict[str, object]:
    async with session_scope() as session:
        state = await kill_switch.get_state(session, tenant_id)
        return _state_to_json(state)


@router.post(
    "/kill-switch/{tenant_id}/disable",
    summary="Emergency disable AI for tenant (二次確認)",
)
async def disable_kill_switch(tenant_id: uuid.UUID, body: DisableRequest) -> dict[str, object]:
    async with session_scope() as session:
        try:
            state = await kill_switch.disable_ai(
                session,
                tenant_id=tenant_id,
                confirm_tenant_id=body.confirm_tenant_id,
                actor_id=body.actor_id,
                reason=body.reason,
            )
        except kill_switch.KillSwitchError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return _state_to_json(state)


@router.post(
    "/kill-switch/{tenant_id}/enable",
    summary="Re-enable AI for tenant",
)
async def enable_kill_switch(tenant_id: uuid.UUID, body: EnableRequest) -> dict[str, object]:
    async with session_scope() as session:
        try:
            state = await kill_switch.enable_ai(
                session,
                tenant_id=tenant_id,
                actor_id=body.actor_id,
                reason=body.reason,
            )
        except kill_switch.KillSwitchError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return _state_to_json(state)
