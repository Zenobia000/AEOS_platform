"""LINE webhook 測試 fixtures — 重用 DB container + monkeypatch session_scope.

Webhook handler 內部用 `session_scope()` 開新 session，無法直接灌
db_session fixture；策略：把 session_scope 換成包裝 fixture 的 session
（避免新建 engine）。
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

import app.api.webhooks.line as line_module
from app.db.base import Base
from app.db.models import (  # noqa: F401  (populate metadata)
    api_key,
    audit_log,
    channel_binding,
    conversation,
    conversation_handoff,
    employee,
    ingestion_job,
    knowledge_card,
    message,
    outbound_message,
    skill,
    skill_binding,
    skill_version,
    tenant,
    tool,
    tool_invocation,
    tool_policy,
    webhook_event,
)
from app.main import app
from tests.db.conftest import _MESSAGE_PARTITION_SQL, _RLS_TRIGGER_SQL


@pytest.fixture(scope="module")
def webhook_pg() -> Iterator[PostgresContainer]:
    container = PostgresContainer(
        "pgvector/pgvector:pg15",
        username="aeos",
        password="aeos_test",
    )
    container.start()
    try:
        yield container
    finally:
        container.stop()


@pytest_asyncio.fixture
async def webhook_engine(webhook_pg: PostgresContainer) -> AsyncIterator[AsyncEngine]:
    url = URL.create(
        drivername="postgresql+asyncpg",
        username=webhook_pg.username,
        password=webhook_pg.password,
        host=webhook_pg.get_container_host_ip(),
        port=int(webhook_pg.get_exposed_port(5432)),
        database=webhook_pg.dbname,
    )
    engine = create_async_engine(url, echo=False, pool_pre_ping=True)
    async with engine.begin() as conn:
        for stmt in _RLS_TRIGGER_SQL[:2]:
            await conn.exec_driver_sql(stmt)
        await conn.run_sync(Base.metadata.create_all)
        for stmt in _RLS_TRIGGER_SQL[2:]:
            await conn.exec_driver_sql(stmt)
        for stmt in _MESSAGE_PARTITION_SQL:
            await conn.exec_driver_sql(stmt)
    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def webhook_session(
    webhook_engine: AsyncEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[AsyncSession]:
    """單一共用 session：先用它建種子資料，再 monkeypatch session_scope
    讓 webhook handler 也用同一個 session（看到種子）。
    """
    sm = async_sessionmaker(bind=webhook_engine, expire_on_commit=False, class_=AsyncSession)
    session = sm()
    try:

        @asynccontextmanager
        async def patched_session_scope(
            tenant_id: str | None = None,
        ) -> AsyncIterator[AsyncSession]:
            yield session

        monkeypatch.setattr(line_module, "session_scope", patched_session_scope)
        yield session
        await session.commit()
    finally:
        await session.close()


@pytest_asyncio.fixture
async def client(webhook_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
