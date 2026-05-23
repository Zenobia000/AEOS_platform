"""Auth service — bcrypt password + bearer token sessions (S5).

對應 S5 §MFA / auth：
- create_account: bcrypt hash password 寫進 expert_account
- verify_password: 對比 plaintext vs hash
- create_session: 隨機 32-byte token base64url → 寫 expert_session（30 天過期）
- lookup_session: 給 token → 找有效 expert（過期 / 帳號 disabled 都拒）
- revoke_session: 刪除 row（登出）

Phase 1 簡化：
- 無 MFA (S6 接 TOTP)
- 無 rate-limit on /login（pilot 上線前可加，Phase 2 用 Redis 計數）
- session 不滑動過期；30 天 hard cutoff 然後重新登入
"""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.expert_account import EXPERT_ROLES, ExpertAccount
from app.db.models.expert_session import ExpertSession

DEFAULT_SESSION_TTL = timedelta(days=30)


class AuthError(RuntimeError):
    """Auth 操作無法執行（憑證錯 / 帳號 disabled / token 無效）."""


@dataclass(frozen=True)
class AuthenticatedExpert:
    """經過驗證的 expert（給 FastAPI dependency 用）."""

    id: uuid.UUID
    email: str
    name: str
    role: str
    tenant_id: uuid.UUID | None


def hash_password(plaintext: str) -> str:
    """bcrypt hash (default cost=12)."""
    if not plaintext:
        raise AuthError("password cannot be empty")
    return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()


def verify_password(plaintext: str, password_hash: str) -> bool:
    if not plaintext or not password_hash:
        return False
    try:
        return bcrypt.checkpw(plaintext.encode(), password_hash.encode())
    except ValueError:
        return False


async def create_account(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    name: str,
    role: str = "expert",
    tenant_id: uuid.UUID | None = None,
) -> ExpertAccount:
    if role not in EXPERT_ROLES:
        raise AuthError(f"invalid role {role!r}; must be one of {EXPERT_ROLES}")
    if not email.strip() or "@" not in email:
        raise AuthError("invalid email")
    if not name.strip():
        raise AuthError("name cannot be empty")

    existing = (
        await session.execute(select(ExpertAccount).where(ExpertAccount.email == email))
    ).scalar_one_or_none()
    if existing is not None:
        raise AuthError(f"expert with email {email!r} already exists")

    account = ExpertAccount(
        email=email.strip().lower(),
        password_hash=hash_password(password),
        name=name.strip(),
        role=role,
        tenant_id=tenant_id,
    )
    session.add(account)
    await session.flush()
    return account


async def login(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    session_ttl: timedelta = DEFAULT_SESSION_TTL,
) -> tuple[ExpertAccount, str]:
    """驗證 email/password；成功回 (account, token).

    Raises:
        AuthError: 帳號不存在 / 密碼錯 / 帳號 disabled（全部一視同仁回
                   'invalid credentials' 避免 user enumeration）
    """
    account = (
        await session.execute(
            select(ExpertAccount).where(ExpertAccount.email == email.strip().lower())
        )
    ).scalar_one_or_none()
    if account is None or not account.enabled:
        raise AuthError("invalid credentials")
    if not verify_password(password, account.password_hash):
        raise AuthError("invalid credentials")

    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    session.add(
        ExpertSession(
            token=token,
            expert_id=account.id,
            expires_at=now + session_ttl,
        )
    )
    account.last_login_at = now
    await session.flush()
    return account, token


async def lookup_session(session: AsyncSession, *, token: str) -> AuthenticatedExpert:
    """token → AuthenticatedExpert；無效 / 過期 / 帳號 disabled raise."""
    if not token:
        raise AuthError("missing token")

    sess = (
        await session.execute(select(ExpertSession).where(ExpertSession.token == token))
    ).scalar_one_or_none()
    if sess is None:
        raise AuthError("invalid token")

    now = datetime.now(UTC)
    if sess.expires_at < now:
        raise AuthError("token expired")

    account = (
        await session.execute(select(ExpertAccount).where(ExpertAccount.id == sess.expert_id))
    ).scalar_one_or_none()
    if account is None or not account.enabled:
        raise AuthError("account disabled")

    # 更新 last_used_at（非 hot path，可接受 write）
    sess.last_used_at = now
    await session.flush()

    return AuthenticatedExpert(
        id=account.id,
        email=account.email,
        name=account.name,
        role=account.role,
        tenant_id=account.tenant_id,
    )


async def revoke_session(session: AsyncSession, *, token: str) -> bool:
    """登出 — 刪除 session row。回 True 表示有刪到。"""
    sess = (
        await session.execute(select(ExpertSession).where(ExpertSession.token == token))
    ).scalar_one_or_none()
    if sess is None:
        return False
    await session.delete(sess)
    await session.flush()
    return True
