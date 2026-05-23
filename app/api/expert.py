"""Expert Console API — Draft Mode 審查端點.

依 PRD-001 §5.4 + API-001 內部 API:
- GET  /api/v1/expert/reviews                  — 列出 awaiting_review 清單
- POST /api/v1/expert/reviews/{id}/approve     — 1-click approve
- POST /api/v1/expert/reviews/{id}/edit        — 編輯後 approve
- POST /api/v1/expert/reviews/{id}/reject      — 拒絕 + 建 handoff

Phase 1 簡化：
- 無 auth（pilot 階段 expert UI 走內網或臨時 token）— S5 接 MFA + RBAC
- expert_id 從 request body 取（之後改成從 session / JWT 拿）
- 無分頁；limit query param 直接控制
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.auth_dependency import current_expert
from app.db.session import session_scope
from app.services import expert_review

router = APIRouter(
    prefix="/api/v1/expert",
    tags=["expert"],
    dependencies=[Depends(current_expert)],
)


# ── Request schemas ────────────────────────────────


class ApproveRequest(BaseModel):
    expert_id: str = Field(min_length=1, max_length=255)


class EditRequest(BaseModel):
    expert_id: str = Field(min_length=1, max_length=255)
    new_content: str = Field(min_length=1)


class RejectRequest(BaseModel):
    expert_id: str = Field(min_length=1, max_length=255)
    reason: str = Field(min_length=1, max_length=500)
    handoff_message: str | None = Field(default=None, max_length=1000)


# ── Endpoints ──────────────────────────────────────


@router.get("/reviews", summary="List awaiting_review outbound messages")
async def list_reviews(
    tenant_id: Annotated[uuid.UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> dict[str, object]:
    async with session_scope() as session:
        items = await expert_review.list_pending(
            session,
            tenant_id=tenant_id,
            limit=limit,
        )
        return {"items": items, "count": len(items)}


@router.post(
    "/reviews/{outbound_id}/approve",
    summary="1-click approve draft",
)
async def approve_review(
    outbound_id: uuid.UUID,
    body: ApproveRequest,
) -> dict[str, object]:
    async with session_scope() as session:
        try:
            result = await expert_review.approve(
                session,
                outbound_id=outbound_id,
                expert_id=body.expert_id,
            )
        except expert_review.ExpertReviewError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return {
            "outbound_id": str(result.outbound_id),
            "action": result.action,
            "new_status": result.new_status,
        }


@router.post(
    "/reviews/{outbound_id}/edit",
    summary="Edit draft content + approve",
)
async def edit_review(
    outbound_id: uuid.UUID,
    body: EditRequest,
) -> dict[str, object]:
    async with session_scope() as session:
        try:
            result = await expert_review.edit_and_approve(
                session,
                outbound_id=outbound_id,
                new_content=body.new_content,
                expert_id=body.expert_id,
            )
        except expert_review.ExpertReviewError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return {
            "outbound_id": str(result.outbound_id),
            "action": result.action,
            "new_status": result.new_status,
        }


@router.post(
    "/reviews/{outbound_id}/reject",
    summary="Reject draft + create conversation_handoff",
)
async def reject_review(
    outbound_id: uuid.UUID,
    body: RejectRequest,
) -> dict[str, object]:
    async with session_scope() as session:
        try:
            result = await expert_review.reject(
                session,
                outbound_id=outbound_id,
                reason=body.reason,
                expert_id=body.expert_id,
                handoff_message=body.handoff_message,
            )
        except expert_review.ExpertReviewError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return {
            "outbound_id": str(result.outbound_id),
            "action": result.action,
            "new_status": result.new_status,
            "handoff_id": str(result.handoff_id) if result.handoff_id else None,
        }
