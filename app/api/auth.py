"""Auth API — login / logout / me (S5).

對應 S5 §MFA / auth。Phase 1：email + password + bearer token。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.auth_dependency import current_expert
from app.db.models.expert_session import ExpertSession
from app.db.session import session_scope
from app.services import auth as auth_service
from app.services.auth import AuthenticatedExpert

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=200)


class LoginResponse(BaseModel):
    token: str
    expires_at: str
    expert: dict[str, object]


@router.post("/login", summary="Email + password → bearer token")
async def login(body: LoginRequest) -> LoginResponse:
    if "@" not in body.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid email")
    async with session_scope() as session:
        try:
            account, token = await auth_service.login(
                session, email=body.email, password=body.password
            )
        except auth_service.AuthError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc

        sess = (
            await session.execute(select(ExpertSession).where(ExpertSession.token == token))
        ).scalar_one()

        return LoginResponse(
            token=token,
            expires_at=sess.expires_at.isoformat(),
            expert={
                "id": str(account.id),
                "email": account.email,
                "name": account.name,
                "role": account.role,
                "tenant_id": str(account.tenant_id) if account.tenant_id else None,
            },
        )


@router.post("/logout", summary="Revoke current bearer token")
async def logout(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    """登出 — revoke 當前 token。Anonymous bypass / 無 token → noop。"""
    if not authorization or not authorization.startswith("Bearer "):
        return {"revoked": False, "reason": "no bearer token"}
    token = authorization[len("Bearer ") :].strip()
    if not token:
        return {"revoked": False, "reason": "empty token"}

    async with session_scope() as session:
        revoked = await auth_service.revoke_session(session, token=token)
        return {"revoked": revoked}


@router.get("/me", summary="Current expert (validates token)")
async def me(
    expert: Annotated[AuthenticatedExpert, Depends(current_expert)],
) -> dict[str, object]:
    return {
        "id": str(expert.id),
        "email": expert.email,
        "name": expert.name,
        "role": expert.role,
        "tenant_id": str(expert.tenant_id) if expert.tenant_id else None,
    }
