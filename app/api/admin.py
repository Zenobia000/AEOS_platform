"""Admin API — kill switch + canary toggle (S5).

Phase 1：受 auth dependency 保護（AEOS_AUTH_REQUIRED=true 時強制）。
- GET  /api/v1/admin/kill-switch/{tenant_id}             — 查 kill switch
- POST /api/v1/admin/kill-switch/{tenant_id}/disable
- POST /api/v1/admin/kill-switch/{tenant_id}/enable
- GET  /api/v1/admin/canary/{tenant_id}                  — 查 canary %
- POST /api/v1/admin/canary/{tenant_id}                  — 設 canary %
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.auth_dependency import current_expert
from app.db.session import session_scope
from app.services import canary, kill_switch

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


# ── Canary toggle ──────────────────────────────────


class CanarySetRequest(BaseModel):
    percent: int = Field(ge=0, le=100)
    actor_id: str = Field(min_length=1, max_length=255)
    reason: str = Field(min_length=1, max_length=500)


@router.get("/canary/{tenant_id}", summary="Get canary percent for tenant")
async def get_canary(tenant_id: uuid.UUID) -> dict[str, object]:
    async with session_scope() as session:
        percent = await canary.get_canary_percent(session, tenant_id=tenant_id)
        return {"tenant_id": str(tenant_id), "canary_percent": percent}


@router.post("/canary/{tenant_id}", summary="Set canary percent for tenant")
async def set_canary(tenant_id: uuid.UUID, body: CanarySetRequest) -> dict[str, object]:
    async with session_scope() as session:
        try:
            state = await canary.set_canary_percent(
                session,
                tenant_id=tenant_id,
                percent=body.percent,
                actor_id=body.actor_id,
                reason=body.reason,
            )
        except canary.CanaryError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return {
            "tenant_id": str(state.tenant_id),
            "canary_percent": state.canary_percent,
        }
