"""DB 測試 fixtures — 使用 testcontainers 跑隔離的 pg+pgvector。

每個測試 module 一個獨立 PG container；不污染本機 dev DB。
Schema 用 SQLAlchemy `create_all` 建（migration 本身另由 alembic 測試覆蓋）。
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from app.db.base import Base
from app.db.models import api_key, audit_log, tenant  # noqa: F401  (populate metadata)

# RLS 與 trigger 的 SQL —— 由 migration 維護，本檔同步在測試 schema 套
_RLS_TRIGGER_SQL = [
    "CREATE EXTENSION IF NOT EXISTS pgcrypto",
    "CREATE EXTENSION IF NOT EXISTS vector",
    "ALTER TABLE tenants ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY tenant_self_isolation ON tenants "
    "USING (id::text = current_setting('app.tenant_id', true))",
    "ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY api_keys_tenant_isolation ON api_keys "
    "USING (tenant_id::text = current_setting('app.tenant_id', true))",
    "ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY audit_logs_tenant_isolation ON audit_logs "
    "USING (tenant_id IS NULL "
    "OR tenant_id::text = current_setting('app.tenant_id', true))",
    "CREATE OR REPLACE FUNCTION audit_logs_block_modify() RETURNS trigger AS $$ "
    "BEGIN RAISE EXCEPTION 'audit_logs is append-only; % not allowed', TG_OP "
    "USING ERRCODE = 'insufficient_privilege'; END; $$ LANGUAGE plpgsql",
    "CREATE TRIGGER audit_logs_block_update BEFORE UPDATE ON audit_logs "
    "FOR EACH ROW EXECUTE FUNCTION audit_logs_block_modify()",
    "CREATE TRIGGER audit_logs_block_delete BEFORE DELETE ON audit_logs "
    "FOR EACH ROW EXECUTE FUNCTION audit_logs_block_modify()",
]


@pytest.fixture(scope="module")
def pg_container() -> Iterator[PostgresContainer]:
    """啟一個 pg+pgvector container，全 module 共用。"""
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
async def db_engine(pg_container: PostgresContainer) -> AsyncIterator[AsyncEngine]:
    """建立 async engine + schema + RLS + trigger。每測試重建以避免污染。"""
    url = URL.create(
        drivername="postgresql+asyncpg",
        username=pg_container.username,
        password=pg_container.password,
        host=pg_container.get_container_host_ip(),
        port=int(pg_container.get_exposed_port(5432)),
        database=pg_container.dbname,
    )
    engine = create_async_engine(url, echo=False, pool_pre_ping=True)

    async with engine.begin() as conn:
        for stmt in _RLS_TRIGGER_SQL[:2]:  # extensions only
            await conn.exec_driver_sql(stmt)
        await conn.run_sync(Base.metadata.create_all)
        for stmt in _RLS_TRIGGER_SQL[2:]:
            await conn.exec_driver_sql(stmt)

    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """每個測試獨立 session；無自動 RLS context。"""
    sm = async_sessionmaker(bind=db_engine, expire_on_commit=False, class_=AsyncSession)
    async with sm() as session:
        yield session
        await session.rollback()
