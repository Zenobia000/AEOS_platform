"""Admin expert account management API integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.expert_account import ExpertAccount
from app.db.models.expert_session import ExpertSession
from app.services import auth as auth_service


async def test_list_experts_returns_seeded(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    await auth_service.create_account(
        webhook_session,
        email="amy@aeos",
        password="hunter22",
        name="Amy",
    )
    resp = await client.get("/api/v1/admin/experts")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1
    emails = {e["email"] for e in body["items"]}
    assert "amy@aeos" in emails


async def test_create_expert_persists_account(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    resp = await client.post(
        "/api/v1/admin/experts",
        json={
            "email": "ben@aeos",
            "password": "secret-1234",
            "name": "Ben",
            "role": "expert",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "ben@aeos"
    assert body["enabled"] is True

    account = (
        await webhook_session.execute(
            select(ExpertAccount).where(ExpertAccount.email == "ben@aeos")
        )
    ).scalar_one()
    assert account.password_hash.startswith("$2b$")


async def test_create_expert_duplicate_email_409(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    await auth_service.create_account(
        webhook_session,
        email="dup@aeos",
        password="x123456",
        name="Dup",
    )
    resp = await client.post(
        "/api/v1/admin/experts",
        json={
            "email": "dup@aeos",
            "password": "x123456",
            "name": "Dup2",
        },
    )
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]


async def test_create_expert_validation_422(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    resp = await client.post(
        "/api/v1/admin/experts",
        json={"email": "x@y", "password": "short", "name": "X"},
    )
    assert resp.status_code == 422  # password min_length=6


async def test_disable_expert_revokes_sessions(
    client: AsyncClient, webhook_session: AsyncSession
) -> None:
    account = await auth_service.create_account(
        webhook_session,
        email="rev@aeos",
        password="x123456",
        name="Rev",
    )
    # 製造一個 active session
    _, token = await auth_service.login(webhook_session, email="rev@aeos", password="x123456")
    await webhook_session.flush()

    resp = await client.post(f"/api/v1/admin/experts/{account.id}/disable")
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False

    # session 應被清掉
    remaining = (
        (
            await webhook_session.execute(
                select(ExpertSession).where(ExpertSession.expert_id == account.id)
            )
        )
        .scalars()
        .all()
    )
    assert list(remaining) == []

    # 之後用 token 應該 lookup_session raise
    with pytest.raises(auth_service.AuthError):
        await auth_service.lookup_session(webhook_session, token=token)


async def test_enable_expert(client: AsyncClient, webhook_session: AsyncSession) -> None:
    account = await auth_service.create_account(
        webhook_session, email="en@aeos", password="x123456", name="E"
    )
    account.enabled = False
    await webhook_session.flush()

    resp = await client.post(f"/api/v1/admin/experts/{account.id}/enable")
    assert resp.status_code == 200
    assert resp.json()["enabled"] is True


async def test_disable_unknown_404(client: AsyncClient, webhook_session: AsyncSession) -> None:
    import uuid as _uuid

    resp = await client.post(f"/api/v1/admin/experts/{_uuid.uuid4()}/disable")
    assert resp.status_code == 404


async def test_admin_endpoints_require_admin_role(
    client: AsyncClient, webhook_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """expert role 帳號登入後叫 admin endpoint 應 403."""
    monkeypatch.setenv("AEOS_AUTH_REQUIRED", "true")
    await auth_service.create_account(
        webhook_session,
        email="ex@aeos",
        password="x123456",
        name="Expert",
        role="expert",
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "ex@aeos", "password": "x123456"},
    )
    token = login.json()["token"]

    resp = await client.get(
        "/api/v1/admin/experts",
        headers={"authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
