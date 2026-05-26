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


# ═══════════════════════════════════════════════════════════
# DLQ — outbound permanent-failure inspector + requeue
# ═══════════════════════════════════════════════════════════

from datetime import UTC, datetime, timedelta  # noqa: E402

from app.db.models.outbound_message import OutboundMessage  # noqa: E402


def _outbound_to_json(m: OutboundMessage) -> dict[str, object]:
    return {
        "id": str(m.id),
        "tenant_id": str(m.tenant_id),
        "conversation_id": str(m.conversation_id),
        "channel": m.channel,
        "status": m.status,
        "retry_count": m.retry_count,
        "error_message": m.error_message,
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "sent_at": m.sent_at.isoformat() if m.sent_at else None,
    }


@router.get(
    "/dlq/outbound",
    summary="List permanently-failed outbound messages (DLQ inspector)",
    dependencies=[Depends(require_admin)],
)
async def list_dlq_outbound(
    tenant_id: uuid.UUID | None = None,
    since_hours: int = 24,
    limit: int = 50,
) -> dict[str, object]:
    """列 status='failed' outbound（permanent fail = DLQ row）。"""
    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="limit must be 1..500",
        )
    cutoff = datetime.now(UTC) - timedelta(hours=max(1, since_hours))

    async with session_scope() as session:
        stmt = select(OutboundMessage).where(
            OutboundMessage.status == "failed",
            OutboundMessage.created_at >= cutoff,
        )
        if tenant_id is not None:
            stmt = stmt.where(OutboundMessage.tenant_id == tenant_id)
        stmt = stmt.order_by(OutboundMessage.created_at.desc()).limit(limit)
        rows = list((await session.execute(stmt)).scalars().all())
        return {
            "items": [_outbound_to_json(m) for m in rows],
            "count": len(rows),
            "since_hours": since_hours,
        }


@router.post(
    "/dlq/outbound/{outbound_id}/requeue",
    summary="手動 requeue DLQ row → status='retrying' + retry_count=0",
    dependencies=[Depends(require_admin)],
)
async def requeue_dlq_outbound(outbound_id: uuid.UUID) -> dict[str, object]:
    async with session_scope() as session:
        m = (
            await session.execute(select(OutboundMessage).where(OutboundMessage.id == outbound_id))
        ).scalar_one_or_none()
        if m is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"outbound {outbound_id} not found",
            )
        if m.status != "failed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"only failed outbound can be requeued, current status: {m.status}",
            )
        from app.services import audit as _audit

        m.status = "retrying"
        m.retry_count = 0
        m.error_message = None
        await session.flush()
        await _audit.emit(
            session,
            event_type="dlq.outbound_requeued",
            tenant_id=m.tenant_id,
            resource_type="outbound_message",
            resource_id=str(m.id),
            payload={"manual": True},
        )
        return _outbound_to_json(m)


# ═══════════════════════════════════════════════════════════
# Skill Registry sync (Phase 1 後續 #24 — MC-005 §Interface)
# ═══════════════════════════════════════════════════════════


from pathlib import Path as _Path  # noqa: E402

from app.services import skill_registry as _skill_registry  # noqa: E402


class SkillSyncRequest(BaseModel):
    """POST /admin/skills/sync body."""

    tenant_id: uuid.UUID
    skills_root: str | None = Field(
        default=None,
        description="絕對或相對於 cwd 的 git monorepo path；None = 預設 ./skills",
    )


@router.post(
    "/skills/sync",
    summary="掃 skills/ git tree → upsert DB skill / skill_version (MC-005 sync_from_git)",
    dependencies=[Depends(require_admin)],
)
async def sync_skills_from_git(req: SkillSyncRequest) -> dict[str, object]:
    """git 內 skill 進到 DB 鏡像。已存在的 skill_version 不會被覆寫
    （DB 是事實鏡像；要改 skill 內容請 bump version + 再 sync）。"""
    root = _Path(req.skills_root) if req.skills_root else _Path("skills")
    async with session_scope() as session:
        result = await _skill_registry.sync_from_git(
            session,
            tenant_id=req.tenant_id,
            skills_root=root,
        )
        return {
            "tenant_id": str(req.tenant_id),
            "skills_root": str(root),
            "skills_inserted": result.skills_inserted,
            "skills_updated": result.skills_updated,
            "versions_inserted": result.versions_inserted,
            "versions_skipped": result.versions_skipped,
            "errors": result.errors,
        }


# ═══════════════════════════════════════════════════════════
# Skill Version 5-state lifecycle promotion API (Phase 1 後續 #8)
# ═══════════════════════════════════════════════════════════


VALID_PROMOTIONS: dict[str, list[str]] = {
    "draft": ["testing", "deprecated"],
    "testing": ["approved", "draft", "deprecated"],
    "approved": ["production", "draft", "deprecated"],
    "production": ["deprecated"],
    "deprecated": [],
}


class SkillPromoteRequest(BaseModel):
    target_status: str = Field(pattern=r"^(draft|testing|approved|production|deprecated)$")
    approved_by: str | None = Field(default=None, max_length=255)
    reason: str = Field(min_length=1, max_length=500)


@router.post(
    "/skills/versions/{version_id}/promote",
    summary="State transition skill_version status (MC-005 5-state lifecycle)",
    dependencies=[Depends(require_admin)],
)
async def promote_skill_version(
    version_id: uuid.UUID, body: SkillPromoteRequest
) -> dict[str, object]:
    """Promote skill_version via 5-state lifecycle:
    draft → testing → approved → production → deprecated

    Quality Gate（MC-005）：
    - target=production 需 approved_by + approved_at + test_pass_rate >= 0.80
    - 違反 DB CHECK constraint 直接 raise

    Audit：寫 `skill.promoted` 含 from/to/reason。
    """
    from sqlalchemy import select as _sel

    from app.db.models.skill_version import SkillVersion
    from app.services import audit as _audit

    async with session_scope() as session:
        sv = (
            await session.execute(_sel(SkillVersion).where(SkillVersion.id == version_id))
        ).scalar_one_or_none()
        if sv is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"skill_version {version_id} not found",
            )

        current = sv.status
        target = body.target_status
        if current == target:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"already in status: {current}",
            )
        allowed = VALID_PROMOTIONS.get(current, [])
        if target not in allowed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"illegal transition {current} → {target}; allowed: {allowed}",
            )

        sv.status = target
        if target in ("approved", "production") and body.approved_by:
            sv.approved_by = body.approved_by
            from datetime import datetime as _dt

            sv.approved_at = _dt.now(UTC)

        try:
            await session.flush()
        except Exception as exc:  # DB CHECK quality gate may fire
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"DB constraint: {type(exc).__name__}",
            ) from exc

        await _audit.emit(
            session,
            event_type="skill.promoted",
            tenant_id=sv.tenant_id,
            actor_id=body.approved_by or "system",
            resource_type="skill_version",
            resource_id=str(sv.id),
            payload={
                "from_status": current,
                "to_status": target,
                "reason": body.reason,
            },
        )

        return {
            "id": str(sv.id),
            "skill_id": str(sv.skill_id),
            "version": sv.version,
            "status": sv.status,
            "approved_by": sv.approved_by,
            "approved_at": sv.approved_at.isoformat() if sv.approved_at else None,
        }


# ═══════════════════════════════════════════════════════════
# Tenant admin CRUD (Phase 1 後續 #9)
# ═══════════════════════════════════════════════════════════


from app.db.models.tenant import Tenant as _Tenant  # noqa: E402


class TenantCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")


def _tenant_to_json(t: _Tenant) -> dict[str, object]:
    return {
        "id": str(t.id),
        "name": t.name,
        "slug": t.slug,
        "status": t.status,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@router.get(
    "/tenants",
    summary="List all tenants",
    dependencies=[Depends(require_admin)],
)
async def list_tenants() -> dict[str, object]:
    from sqlalchemy import select as _sel

    async with session_scope() as session:
        rows = list(
            (await session.execute(_sel(_Tenant).order_by(_Tenant.created_at.desc()))).scalars()
        )
        return {"items": [_tenant_to_json(t) for t in rows], "count": len(rows)}


@router.post(
    "/tenants",
    summary="Create tenant",
    dependencies=[Depends(require_admin)],
)
async def create_tenant(body: TenantCreateRequest) -> dict[str, object]:
    async with session_scope() as session:
        t = _Tenant(name=body.name, slug=body.slug)
        session.add(t)
        try:
            await session.flush()
        except Exception as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"create failed: {type(exc).__name__}",
            ) from exc
        return _tenant_to_json(t)


@router.post(
    "/tenants/{tenant_id}/suspend",
    summary="Suspend tenant (active → suspended)",
    dependencies=[Depends(require_admin)],
)
async def suspend_tenant(tenant_id: uuid.UUID) -> dict[str, object]:
    from sqlalchemy import select as _sel

    async with session_scope() as session:
        t = (
            await session.execute(_sel(_Tenant).where(_Tenant.id == tenant_id))
        ).scalar_one_or_none()
        if t is None:
            raise HTTPException(status_code=404, detail="tenant not found")
        if t.status not in ("active", "pending"):
            raise HTTPException(
                status_code=409,
                detail=f"only active/pending can be suspended (current: {t.status})",
            )
        t.status = "suspended"
        await session.flush()
        return _tenant_to_json(t)


@router.post(
    "/tenants/{tenant_id}/archive",
    summary="Archive tenant (active/suspended → archived; MC-004 4-state)",
    dependencies=[Depends(require_admin)],
)
async def archive_tenant(tenant_id: uuid.UUID) -> dict[str, object]:
    from sqlalchemy import select as _sel

    async with session_scope() as session:
        t = (
            await session.execute(_sel(_Tenant).where(_Tenant.id == tenant_id))
        ).scalar_one_or_none()
        if t is None:
            raise HTTPException(status_code=404, detail="tenant not found")
        if t.status == "archived":
            raise HTTPException(status_code=409, detail="already archived")
        t.status = "archived"
        await session.flush()
        return _tenant_to_json(t)
