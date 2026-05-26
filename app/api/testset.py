"""TestSet REST API — case CRUD + run lifecycle (S3 / AC-001).

對應 PRD-001 §5.2 F-TS-01/02/03。Phase 1 無 auth；S5 接 MFA + RBAC。

Endpoints:
- GET    /api/v1/testset/cases?tenant_id=&enabled_only=true
- POST   /api/v1/testset/cases
- POST   /api/v1/testset/cases/{case_id}/disable
- POST   /api/v1/testset/runs
- GET    /api/v1/testset/runs/{run_id}
- GET    /api/v1/testset/runs/{run_id}/cases
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.auth_dependency import current_expert
from app.db.models.test_case import TestCase
from app.db.models.test_run_case import TestRunCase
from app.db.session import session_scope
from app.services import test_set

router = APIRouter(
    prefix="/api/v1/testset",
    tags=["testset"],
    dependencies=[Depends(current_expert)],
)


class CaseCreateRequest(BaseModel):
    tenant_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    user_input: str = Field(min_length=1)
    expected_outcome: str = Field(min_length=1)
    expected_keywords: list[str] = Field(default_factory=list)
    created_by: str | None = Field(default=None, max_length=255)
    skill_slug: str | None = Field(default=None, max_length=200)


class RunCreateRequest(BaseModel):
    tenant_id: uuid.UUID
    skill_slug: str = Field(min_length=1)
    skill_version: str = Field(min_length=1)
    created_by: str | None = Field(default=None, max_length=255)


def _case_to_json(tc: TestCase) -> dict[str, object]:
    return {
        "case_id": str(tc.id),
        "tenant_id": str(tc.tenant_id),
        "name": tc.name,
        "user_input": tc.user_input,
        "expected_outcome": tc.expected_outcome,
        "expected_keywords": list(tc.expected_keywords),
        "enabled": tc.enabled,
        "skill_slug": tc.skill_slug,
        "created_by": tc.created_by,
        "created_at": tc.created_at.isoformat() if tc.created_at else None,
    }


def _run_summary_to_json(summary: test_set.RunSummary) -> dict[str, object]:
    return {
        "run_id": str(summary.run_id),
        "status": summary.status,
        "total_cases": summary.total_cases,
        "passed_cases": summary.passed_cases,
        "failed_cases": summary.failed_cases,
        "pass_rate": summary.pass_rate,
    }


# ── Cases ──────────────────────────────────────────


@router.get("/cases", summary="List test cases for tenant (optionally filtered by skill_slug)")
async def list_cases(
    tenant_id: Annotated[uuid.UUID, Query()],
    enabled_only: Annotated[bool, Query()] = True,
    skill_slug: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> dict[str, object]:
    """skill_slug: 提供時列該 skill + NULL 通用題；None / _all_ = 全列。"""
    effective_skill = None if skill_slug in (None, "_all_") else skill_slug
    async with session_scope() as session:
        rows = await test_set.list_test_cases(
            session,
            tenant_id=tenant_id,
            enabled_only=enabled_only,
            skill_slug=effective_skill,
            limit=limit,
        )
        items = [_case_to_json(tc) for tc in rows]
        return {"items": items, "count": len(items)}


@router.post("/cases", summary="Create test case")
async def create_case(body: CaseCreateRequest) -> dict[str, object]:
    async with session_scope() as session:
        try:
            tc = await test_set.create_test_case(
                session,
                tenant_id=body.tenant_id,
                name=body.name,
                user_input=body.user_input,
                expected_outcome=body.expected_outcome,
                expected_keywords=body.expected_keywords,
                created_by=body.created_by,
                skill_slug=body.skill_slug,
            )
        except test_set.TestSetError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return _case_to_json(tc)


@router.post("/cases/{case_id}/disable", summary="Disable test case")
async def disable_case(case_id: uuid.UUID) -> dict[str, object]:
    async with session_scope() as session:
        try:
            tc = await test_set.disable_test_case(session, test_case_id=case_id)
        except test_set.TestSetError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        return _case_to_json(tc)


# ── Runs ───────────────────────────────────────────


@router.post("/runs", summary="Create test run (pending)")
async def create_run(body: RunCreateRequest) -> dict[str, object]:
    async with session_scope() as session:
        try:
            run = await test_set.create_test_run(
                session,
                tenant_id=body.tenant_id,
                skill_slug=body.skill_slug,
                skill_version=body.skill_version,
                created_by=body.created_by,
            )
        except test_set.TestSetError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return {
            "run_id": str(run.id),
            "status": run.status,
            "total_cases": run.total_cases,
            "skill_slug": run.skill_slug,
            "skill_version": run.skill_version,
        }


@router.get("/runs/{run_id}", summary="Get run summary")
async def get_run(run_id: uuid.UUID) -> dict[str, object]:
    async with session_scope() as session:
        try:
            summary = await test_set.get_run_summary(session, run_id=run_id)
        except test_set.TestSetError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        return _run_summary_to_json(summary)


@router.get("/runs/{run_id}/cases", summary="Get per-case results for run")
async def get_run_cases(run_id: uuid.UUID) -> dict[str, object]:
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(TestRunCase, TestCase)
                .join(TestCase, TestRunCase.test_case_id == TestCase.id)
                .where(TestRunCase.test_run_id == run_id)
            )
        ).all()
        items = [
            {
                "case_id": str(tc.id),
                "name": tc.name,
                "user_input": tc.user_input,
                "status": trc.status,
                "actual_output": trc.actual_output,
                "judge_score": trc.judge_score,
                "judge_reason": trc.judge_reason,
                "executed_at": trc.executed_at.isoformat() if trc.executed_at else None,
            }
            for trc, tc in rows
        ]
        return {"items": items, "count": len(items)}
