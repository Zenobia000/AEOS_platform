"""Auth service unit tests — hash / verify / login / lookup / revoke."""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.expert_account import ExpertAccount
from app.db.models.expert_session import ExpertSession
from app.services import auth


def test_hash_and_verify_password_round_trip() -> None:
    h = auth.hash_password("hunter2")
    assert h != "hunter2"
    assert h.startswith("$2b$")
    assert auth.verify_password("hunter2", h) is True
    assert auth.verify_password("wrong", h) is False


def test_hash_empty_raises() -> None:
    with pytest.raises(auth.AuthError, match="empty"):
        auth.hash_password("")


def test_verify_safe_against_malformed_hash() -> None:
    assert auth.verify_password("any", "not-a-bcrypt") is False
    assert auth.verify_password("", "anything") is False


async def test_create_account_persists(db_session: AsyncSession) -> None:
    account = await auth.create_account(
        db_session,
        email="amy@example.com",
        password="secret-1234",
        name="Amy",
        role="expert",
    )
    refreshed = (
        await db_session.execute(select(ExpertAccount).where(ExpertAccount.id == account.id))
    ).scalar_one()
    assert refreshed.email == "amy@example.com"
    assert refreshed.password_hash.startswith("$2b$")
    assert refreshed.role == "expert"
    assert refreshed.enabled is True


async def test_create_account_duplicate_email_raises(
    db_session: AsyncSession,
) -> None:
    await auth.create_account(db_session, email="dup@example.com", password="p", name="A")
    with pytest.raises(auth.AuthError, match="already exists"):
        await auth.create_account(db_session, email="dup@example.com", password="p", name="B")


async def test_create_account_invalid_email_raises(
    db_session: AsyncSession,
) -> None:
    with pytest.raises(auth.AuthError, match="invalid email"):
        await auth.create_account(db_session, email="no-at-sign", password="p", name="A")


async def test_login_happy_path(db_session: AsyncSession) -> None:
    await auth.create_account(db_session, email="ben@example.com", password="strong-pw", name="Ben")
    account, token = await auth.login(db_session, email="ben@example.com", password="strong-pw")
    assert account.email == "ben@example.com"
    assert len(token) >= 30
    assert account.last_login_at is not None

    sess = (
        await db_session.execute(select(ExpertSession).where(ExpertSession.token == token))
    ).scalar_one()
    assert sess.expert_id == account.id


async def test_login_wrong_password(db_session: AsyncSession) -> None:
    await auth.create_account(db_session, email="ben2@example.com", password="strong", name="B")
    with pytest.raises(auth.AuthError, match="invalid credentials"):
        await auth.login(db_session, email="ben2@example.com", password="wrong")


async def test_login_unknown_email(db_session: AsyncSession) -> None:
    with pytest.raises(auth.AuthError, match="invalid credentials"):
        await auth.login(db_session, email="ghost@example.com", password="x")


async def test_login_disabled_account(db_session: AsyncSession) -> None:
    account = await auth.create_account(
        db_session, email="disabled@example.com", password="p", name="D"
    )
    account.enabled = False
    await db_session.flush()
    with pytest.raises(auth.AuthError, match="invalid credentials"):
        await auth.login(db_session, email="disabled@example.com", password="p")


async def test_lookup_session_returns_expert(db_session: AsyncSession) -> None:
    await auth.create_account(db_session, email="cathy@example.com", password="pw", name="Cathy")
    _, token = await auth.login(db_session, email="cathy@example.com", password="pw")
    me = await auth.lookup_session(db_session, token=token)
    assert me.email == "cathy@example.com"
    assert me.name == "Cathy"


async def test_lookup_invalid_token_raises(db_session: AsyncSession) -> None:
    with pytest.raises(auth.AuthError, match="invalid token"):
        await auth.lookup_session(db_session, token="not-a-real-token")


async def test_lookup_expired_token_raises(db_session: AsyncSession) -> None:
    await auth.create_account(db_session, email="exp@example.com", password="pw", name="E")
    _, token = await auth.login(
        db_session,
        email="exp@example.com",
        password="pw",
        session_ttl=timedelta(seconds=-10),  # 立刻過期
    )
    with pytest.raises(auth.AuthError, match="expired"):
        await auth.lookup_session(db_session, token=token)


async def test_lookup_with_disabled_account_raises(
    db_session: AsyncSession,
) -> None:
    account = await auth.create_account(
        db_session, email="will-disable@example.com", password="pw", name="W"
    )
    _, token = await auth.login(db_session, email="will-disable@example.com", password="pw")
    account.enabled = False
    await db_session.flush()
    with pytest.raises(auth.AuthError, match="account disabled"):
        await auth.lookup_session(db_session, token=token)


async def test_revoke_session_removes_row(db_session: AsyncSession) -> None:
    await auth.create_account(db_session, email="logout@example.com", password="pw", name="L")
    _, token = await auth.login(db_session, email="logout@example.com", password="pw")
    assert await auth.revoke_session(db_session, token=token) is True
    with pytest.raises(auth.AuthError, match="invalid token"):
        await auth.lookup_session(db_session, token=token)


async def test_revoke_unknown_token_noop(db_session: AsyncSession) -> None:
    assert await auth.revoke_session(db_session, token="ghost") is False
