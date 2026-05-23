"""FastAPI dependency — `Depends(current_expert)` 守衛 endpoint.

行為：
- 從 Authorization: Bearer <token> 取 token
- 透過 services.auth.lookup_session 驗證
- 成功 → 注入 AuthenticatedExpert
- 失敗 → 401 / 403

Bypass for dev / tests:
- 環境變數 `AEOS_AUTH_REQUIRED=false`（預設）→ 回 anonymous bypass expert
- 設 `AEOS_AUTH_REQUIRED=true` 才開始強制 auth（pilot 上線前必設）

這樣讓既有 308 個測試不必全部加 auth header，並讓 dev demo 仍可不登入直接玩。
"""

from __future__ import annotations

import os
import uuid

from fastapi import Header, HTTPException, status

from app.db.session import session_scope
from app.services import auth as auth_service
from app.services.auth import AuthenticatedExpert

# 內建 anonymous bypass expert（auth 未強制時用）
_ANONYMOUS_EXPERT = AuthenticatedExpert(
    id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
    email="anonymous@local",
    name="anonymous (auth bypass)",
    role="admin",
    tenant_id=None,
)


def auth_required() -> bool:
    """是否強制 auth（環境變數驅動）."""
    return os.environ.get("AEOS_AUTH_REQUIRED", "false").lower() in (
        "true",
        "1",
        "yes",
    )


async def current_expert(
    authorization: str | None = Header(default=None),
) -> AuthenticatedExpert:
    """取得當前 expert。

    若 AEOS_AUTH_REQUIRED=false 且無 token → 回 anonymous bypass。
    若有 token，無論 AEOS_AUTH_REQUIRED → 都驗證（防止 token 偽造）。
    """
    token: str | None = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer ") :].strip() or None

    if token is None:
        if auth_required():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="missing Bearer token",
            )
        return _ANONYMOUS_EXPERT

    async with session_scope() as session:
        try:
            return await auth_service.lookup_session(session, token=token)
        except auth_service.AuthError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc


async def require_admin(
    expert: AuthenticatedExpert,
) -> AuthenticatedExpert:
    """進一步限制為 admin role（給 kill switch / 帳號管理 用）."""
    if expert.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin role required",
        )
    return expert
