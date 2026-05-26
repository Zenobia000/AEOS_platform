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

from app.api.auth_dependency import current_expert, require_admin
from app.db.models.expert_account import ExpertAccount
from app.db.models.expert_session import ExpertSession
from app.db.session import session_scope
from app.services import auth as auth_service
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


# ── Expert account management ───────────────────────


class ExpertCreateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=200)
    name: str = Field(min_length=1, max_length=200)
    role: str = Field(default="expert", pattern=r"^(expert|admin)$")
    tenant_id: uuid.UUID | None = Field(default=None)


def _expert_to_json(account: ExpertAccount) -> dict[str, object]:
    return {
        "id": str(account.id),
        "email": account.email,
        "name": account.name,
        "role": account.role,
        "tenant_id": (str(account.tenant_id) if account.tenant_id else None),
        "enabled": account.enabled,
        "last_login_at": (account.last_login_at.isoformat() if account.last_login_at else None),
        "created_at": account.created_at.isoformat(),
    }


@router.get(
    "/experts",
    summary="List expert accounts",
    dependencies=[Depends(require_admin)],
)
async def list_experts() -> dict[str, object]:
    from sqlalchemy import select

    async with session_scope() as session:
        rows = list(
            (await session.execute(select(ExpertAccount).order_by(ExpertAccount.created_at.desc())))
            .scalars()
            .all()
        )
        return {"items": [_expert_to_json(a) for a in rows], "count": len(rows)}


@router.post(
    "/experts",
    summary="Create expert account",
    dependencies=[Depends(require_admin)],
)
async def create_expert(body: ExpertCreateRequest) -> dict[str, object]:
    async with session_scope() as session:
        try:
            account = await auth_service.create_account(
                session,
                email=body.email,
                password=body.password,
                name=body.name,
                role=body.role,
                tenant_id=body.tenant_id,
            )
        except auth_service.AuthError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return _expert_to_json(account)


@router.post(
    "/experts/{expert_id}/disable",
    summary="Disable expert account (login blocked + active sessions revoked)",
    dependencies=[Depends(require_admin)],
)
async def disable_expert(expert_id: uuid.UUID) -> dict[str, object]:
    from sqlalchemy import delete, select

    async with session_scope() as session:
        account = (
            await session.execute(select(ExpertAccount).where(ExpertAccount.id == expert_id))
        ).scalar_one_or_none()
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"expert {expert_id} not found",
            )
        account.enabled = False
        # 同步 revoke 所有 active sessions
        await session.execute(delete(ExpertSession).where(ExpertSession.expert_id == expert_id))
        await session.flush()
        return _expert_to_json(account)


@router.post(
    "/experts/{expert_id}/enable",
    summary="Re-enable expert account",
    dependencies=[Depends(require_admin)],
)
async def enable_expert(expert_id: uuid.UUID) -> dict[str, object]:
    from sqlalchemy import select

    async with session_scope() as session:
        account = (
            await session.execute(select(ExpertAccount).where(ExpertAccount.id == expert_id))
        ).scalar_one_or_none()
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"expert {expert_id} not found",
            )
        account.enabled = True
        await session.flush()
        return _expert_to_json(account)


# ═══════════════════════════════════════════════════════════
# CR-0001 #6 — Skill binding admin API
# ═══════════════════════════════════════════════════════════

from typing import Any  # noqa: E402

from sqlalchemy import select  # noqa: E402

from app.db.models.skill import Skill  # noqa: E402
from app.db.models.skill_binding import SkillBinding  # noqa: E402
from app.db.models.skill_version import SkillVersion  # noqa: E402


class SkillBindingRequest(BaseModel):
    """POST /admin/skills/bindings 請求 body."""

    tenant_id: uuid.UUID
    employee_id: uuid.UUID
    skill_version_id: uuid.UUID
    routing_rule: dict[str, Any] = Field(default_factory=dict)
    is_default: bool = False
    priority: int = 0


class RoutePreviewRequest(BaseModel):
    """POST /admin/skills/route-preview — 給訊息預覽 routing 結果（不實際送）。"""

    employee_id: uuid.UUID
    tenant_id: uuid.UUID
    message: str = Field(min_length=1, max_length=2000)
    channel_id: str | None = None


def _binding_to_json(b: SkillBinding) -> dict[str, object]:
    return {
        "id": str(b.id),
        "tenant_id": str(b.tenant_id),
        "employee_id": str(b.employee_id),
        "skill_version_id": str(b.skill_version_id),
        "routing_rule": b.routing_rule,
        "is_default": b.is_default,
        "priority": b.priority,
        "created_at": b.created_at.isoformat() if b.created_at else None,
    }


@router.get(
    "/skills/{tenant_id}",
    summary="List tenant 的所有 skills + bindings (CR-0001 #6)",
    dependencies=[Depends(require_admin)],
)
async def list_tenant_skills(tenant_id: uuid.UUID) -> dict[str, object]:
    async with session_scope() as session:
        skills_q = await session.execute(select(Skill).where(Skill.tenant_id == tenant_id))
        skills = list(skills_q.scalars())

        skill_versions_q = await session.execute(
            select(SkillVersion).where(SkillVersion.tenant_id == tenant_id)
        )
        skill_versions = list(skill_versions_q.scalars())

        bindings_q = await session.execute(
            select(SkillBinding).where(SkillBinding.tenant_id == tenant_id)
        )
        bindings = list(bindings_q.scalars())

        return {
            "tenant_id": str(tenant_id),
            "skills": [
                {
                    "id": str(s.id),
                    "slug": s.slug,
                    "vertical": s.vertical,
                    "name": s.name,
                    "current_production_version": s.current_production_version,
                }
                for s in skills
            ],
            "skill_versions": [
                {
                    "id": str(sv.id),
                    "skill_id": str(sv.skill_id),
                    "version": sv.version,
                    "status": sv.status,
                }
                for sv in skill_versions
            ],
            "bindings": [_binding_to_json(b) for b in bindings],
        }


@router.post(
    "/skills/bindings",
    summary="建立或更新 skill binding (CR-0001 #6)",
    dependencies=[Depends(require_admin)],
)
async def create_skill_binding(req: SkillBindingRequest) -> dict[str, object]:
    """同 (employee_id, skill_version_id) 視為 upsert 更新 routing_rule + is_default + priority。"""
    async with session_scope() as session:
        existing = (
            await session.execute(
                select(SkillBinding).where(
                    SkillBinding.employee_id == req.employee_id,
                    SkillBinding.skill_version_id == req.skill_version_id,
                )
            )
        ).scalar_one_or_none()

        if existing is not None:
            existing.routing_rule = req.routing_rule
            existing.is_default = req.is_default
            existing.priority = req.priority
            await session.flush()
            return _binding_to_json(existing)

        binding = SkillBinding(
            tenant_id=req.tenant_id,
            employee_id=req.employee_id,
            skill_version_id=req.skill_version_id,
            routing_rule=req.routing_rule,
            is_default=req.is_default,
            priority=req.priority,
        )
        session.add(binding)
        await session.flush()
        return _binding_to_json(binding)


@router.delete(
    "/skills/bindings/{binding_id}",
    summary="刪除 skill binding (CR-0001 #6)",
    dependencies=[Depends(require_admin)],
)
async def delete_skill_binding(binding_id: uuid.UUID) -> dict[str, object]:
    async with session_scope() as session:
        b = (
            await session.execute(select(SkillBinding).where(SkillBinding.id == binding_id))
        ).scalar_one_or_none()
        if b is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"binding {binding_id} not found",
            )
        await session.delete(b)
        await session.flush()
        return {"deleted": str(binding_id)}


@router.post(
    "/skills/route-preview",
    summary="Dev: 給訊息預覽 routing 結果，不實際送 (CR-0001 #6)",
    dependencies=[Depends(require_admin)],
)
async def preview_routing(req: RoutePreviewRequest) -> dict[str, object]:
    """直接呼叫 SkillRouter.route()，回 decision 結構；不啟動 DraftProcessor。"""
    from app.skill import NoSkillBoundError, SkillRouter

    async with session_scope() as session:
        router_svc = SkillRouter(session)
        try:
            decision = await router_svc.route(
                message=req.message,
                employee_id=req.employee_id,
                tenant_id=req.tenant_id,
                channel_id=req.channel_id,
            )
        except NoSkillBoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"no skill bound: {exc}",
            ) from exc
        return {
            "skill_version_id": str(decision.skill_version.id),
            "skill_slug": decision.skill_slug,
            "skill_version_str": decision.skill_version_str,
            "matched_rule_type": decision.matched_rule_type,
            "matched_rule": decision.matched_rule,
        }
