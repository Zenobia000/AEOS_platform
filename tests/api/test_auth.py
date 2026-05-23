"""Auth API integration tests — /login /logout /me + bypass / required modes."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import auth as auth_service


@pytest.fixture
async def seeded_expert(webhook_session: AsyncSession) -> dict[str, str]:
    """先建一個 expert account 給 login 測試用."""
    await auth_service.create_account(
        webhook_session,
        email="alice@example.com",
        password="hunter2-strong",
        name="Alice",
        role="expert",
    )
    return {"email": "alice@example.com", "password": "hunter2-strong"}


async def test_login_returns_token(client: AsyncClient, seeded_expert: dict[str, str]) -> None:
    resp = await client.post("/api/v1/auth/login", json=seeded_expert)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["token"]) >= 30
    assert body["expert"]["email"] == "alice@example.com"
    assert body["expert"]["role"] == "expert"


async def test_login_wrong_password_401(client: AsyncClient, seeded_expert: dict[str, str]) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": seeded_expert["email"], "password": "wrong"},
    )
    assert resp.status_code == 401


async def test_login_invalid_email_400(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "no-at-sign", "password": "pw"},
    )
    assert resp.status_code == 400


async def test_me_returns_expert_with_bearer(
    client: AsyncClient, seeded_expert: dict[str, str]
) -> None:
    login = await client.post("/api/v1/auth/login", json=seeded_expert)
    token = login.json()["token"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "alice@example.com"


async def test_me_anonymous_bypass_when_auth_not_required(
    client: AsyncClient,
) -> None:
    """無 token + AEOS_AUTH_REQUIRED 未設 → 回 anonymous bypass."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == "anonymous@local"


async def test_me_requires_token_when_auth_required(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AEOS_AUTH_REQUIRED", "true")
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_invalid_token_401_regardless_of_bypass(
    client: AsyncClient,
) -> None:
    """有 token 但偽造 → 必須驗證 + 401（防 token 偽造繞過 bypass）."""
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"authorization": "Bearer fake-token-not-real"},
    )
    assert resp.status_code == 401


async def test_logout_revokes_token(client: AsyncClient, seeded_expert: dict[str, str]) -> None:
    login = await client.post("/api/v1/auth/login", json=seeded_expert)
    token = login.json()["token"]
    headers = {"authorization": f"Bearer {token}"}

    logout = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout.status_code == 200
    assert logout.json()["revoked"] is True

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 401


async def test_logout_without_token_noop(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["revoked"] is False


async def test_protected_endpoint_blocks_when_auth_required(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AEOS_AUTH_REQUIRED=true 後 expert/kc/admin/testset 都需 token."""
    monkeypatch.setenv("AEOS_AUTH_REQUIRED", "true")
    resp = await client.get("/api/v1/expert/reviews")
    assert resp.status_code == 401


async def test_protected_endpoint_works_with_valid_token(
    client: AsyncClient,
    seeded_expert: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """有效 token → 通過 auth + 後續邏輯（empty list）."""
    monkeypatch.setenv("AEOS_AUTH_REQUIRED", "true")
    login = await client.post("/api/v1/auth/login", json=seeded_expert)
    token = login.json()["token"]
    resp = await client.get(
        "/api/v1/expert/reviews",
        headers={"authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
