"""KC Review API — KnowledgeCard draft 審查端點.

依 PRD-001 §5.1 F-KB-04 + MC-008:
- GET  /api/v1/kc/drafts                  — 列出 draft KC
- POST /api/v1/kc/drafts/{id}/approve     — 1-click approve
- POST /api/v1/kc/drafts/{id}/edit        — 編輯欄位 + approve
- POST /api/v1/kc/drafts/{id}/archive     — archive（draft / approved 皆可）

Phase 1：無 auth；expert_id 走 request body。S5 接 MFA + RBAC 後改 server-side。
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.db.session import session_scope
from app.services import kc_review

router = APIRouter(prefix="/api/v1/kc", tags=["kc"])


class ApproveRequest(BaseModel):
    expert_id: str = Field(min_length=1, max_length=255)


class EditRequest(BaseModel):
    expert_id: str = Field(min_length=1, max_length=255)
    title: str | None = Field(default=None, min_length=1)
    body_markdown: str | None = Field(default=None, min_length=1)
    tags: list[str] | None = Field(default=None)
    card_type: str | None = Field(default=None)


class ArchiveRequest(BaseModel):
    expert_id: str = Field(min_length=1, max_length=255)
    reason: str = Field(min_length=1, max_length=500)


@router.get("/drafts", summary="List draft knowledge cards")
async def list_drafts(
    tenant_id: Annotated[uuid.UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> dict[str, object]:
    async with session_scope() as session:
        items = await kc_review.list_drafts(session, tenant_id=tenant_id, limit=limit)
        return {"items": items, "count": len(items)}


@router.post("/drafts/{kc_id}/approve", summary="1-click approve KC draft")
async def approve(kc_id: uuid.UUID, body: ApproveRequest) -> dict[str, object]:
    async with session_scope() as session:
        try:
            result = await kc_review.approve(session, kc_id=kc_id, expert_id=body.expert_id)
        except kc_review.KCReviewError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return {
            "kc_id": str(result.kc_id),
            "action": result.action,
            "new_status": result.new_status,
        }


@router.post("/drafts/{kc_id}/edit", summary="Edit KC fields + approve")
async def edit(kc_id: uuid.UUID, body: EditRequest) -> dict[str, object]:
    async with session_scope() as session:
        try:
            result = await kc_review.edit_and_approve(
                session,
                kc_id=kc_id,
                expert_id=body.expert_id,
                title=body.title,
                body_markdown=body.body_markdown,
                tags=body.tags,
                card_type=body.card_type,
            )
        except kc_review.KCReviewError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return {
            "kc_id": str(result.kc_id),
            "action": result.action,
            "new_status": result.new_status,
        }


@router.post("/drafts/{kc_id}/archive", summary="Archive KC")
async def archive(kc_id: uuid.UUID, body: ArchiveRequest) -> dict[str, object]:
    async with session_scope() as session:
        try:
            result = await kc_review.archive(
                session,
                kc_id=kc_id,
                expert_id=body.expert_id,
                reason=body.reason,
            )
        except kc_review.KCReviewError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return {
            "kc_id": str(result.kc_id),
            "action": result.action,
            "new_status": result.new_status,
        }
