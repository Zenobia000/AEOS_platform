"""app.db.session 模組單元測試 — 測 engine/session_scope/set_tenant_context."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import URL
from testcontainers.postgres import PostgresContainer

import app.db.session as db_session_module
from app.config import get_settings


@pytest_asyncio.fixture
async def settings_override(
    pg_container: PostgresContainer,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[None]:
    """把 DATABASE_URL 環境變數指到 testcontainer，並 reset session 模組全域狀態。"""
    url = URL.create(
        drivername="postgresql+asyncpg",
        username=pg_container.username,
        password=pg_container.password,
        host=pg_container.get_container_host_ip(),
        port=int(pg_container.get_exposed_port(5432)),
        database=pg_container.dbname,
    ).render_as_string(hide_password=False)

    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()

    original_engine = db_session_module._engine
    original_sm = db_session_module._sessionmaker
    db_session_module._engine = None
    db_session_module._sessionmaker = None

    try:
        yield
    finally:
        if db_session_module._engine is not None:
            await db_session_module.dispose_engine()
        db_session_module._engine = original_engine
        db_session_module._sessionmaker = original_sm
        get_settings.cache_clear()


async def test_get_engine_singleton(settings_override: None) -> None:
    """get_engine 第一次建、後續 cache。"""
    e1 = db_session_module.get_engine()
    e2 = db_session_module.get_engine()
    assert e1 is e2


async def test_get_sessionmaker_singleton(settings_override: None) -> None:
    sm1 = db_session_module.get_sessionmaker()
    sm2 = db_session_module.get_sessionmaker()
    assert sm1 is sm2


async def test_session_scope_yields_session(settings_override: None) -> None:
    """session_scope 可正常開啟、commit、查 server time。"""
    async with db_session_module.session_scope() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1


async def test_session_scope_with_tenant_context(settings_override: None) -> None:
    """session_scope(tenant_id=...) 注入 RLS context。"""
    tid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    async with db_session_module.session_scope(tenant_id=tid) as session:
        got = await session.execute(text("SELECT current_setting('app.tenant_id', true)"))
        assert got.scalar_one() == tid


async def test_session_scope_rolls_back_on_error(settings_override: None) -> None:
    """transaction 內 raise → 自動 rollback。"""
    with pytest.raises(RuntimeError, match="boom"):
        async with db_session_module.session_scope() as session:
            await session.execute(text("SELECT 1"))
            raise RuntimeError("boom")


async def test_dispose_engine_resets_singleton(settings_override: None) -> None:
    db_session_module.get_engine()
    assert db_session_module._engine is not None
    await db_session_module.dispose_engine()
    assert db_session_module._engine is None
