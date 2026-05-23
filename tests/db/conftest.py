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
from app.db.models import (  # noqa: F401  (populate metadata)
    api_key,
    audit_log,
    channel_binding,
    conversation,
    conversation_handoff,
    employee,
    expert_account,
    expert_session,
    ingestion_job,
    knowledge_card,
    message,
    outbound_message,
    skill,
    skill_binding,
    skill_version,
    tenant,
    tenant_setting,
    test_case,
    test_run,
    test_run_case,
    tool,
    tool_invocation,
    tool_policy,
    webhook_event,
)

# RLS 與 trigger 的 SQL —— 由 migration 維護，本檔同步在測試 schema 套
# 表名單數（依 db-schema.md §1 命名 convention）
_RLS_TRIGGER_SQL = [
    "CREATE EXTENSION IF NOT EXISTS pgcrypto",
    "CREATE EXTENSION IF NOT EXISTS vector",
    "ALTER TABLE tenant ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY tenant_self_isolation ON tenant "
    "USING (id::text = current_setting('app.tenant_id', true))",
    "ALTER TABLE api_key ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY api_key_tenant_isolation ON api_key "
    "USING (tenant_id::text = current_setting('app.tenant_id', true))",
    "ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY audit_log_tenant_isolation ON audit_log "
    "USING (tenant_id IS NULL "
    "OR tenant_id::text = current_setting('app.tenant_id', true))",
    "CREATE OR REPLACE FUNCTION audit_log_block_modify() RETURNS trigger AS $$ "
    "BEGIN RAISE EXCEPTION 'audit_log is append-only; % not allowed', TG_OP "
    "USING ERRCODE = 'insufficient_privilege'; END; $$ LANGUAGE plpgsql",
    "CREATE TRIGGER audit_log_block_update BEFORE UPDATE ON audit_log "
    "FOR EACH ROW EXECUTE FUNCTION audit_log_block_modify()",
    "CREATE TRIGGER audit_log_block_delete BEFORE DELETE ON audit_log "
    "FOR EACH ROW EXECUTE FUNCTION audit_log_block_modify()",
    # knowledge_card + ingestion_job RLS（migration be041f897325 同步）
    "ALTER TABLE knowledge_card ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY knowledge_card_tenant_isolation ON knowledge_card "
    "USING (tenant_id::text = current_setting('app.tenant_id', true))",
    "ALTER TABLE ingestion_job ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY ingestion_job_tenant_isolation ON ingestion_job "
    "USING (tenant_id::text = current_setting('app.tenant_id', true))",
    # ivfflat / GIN indexes（讓 vector / array 查詢能用上）
    "CREATE INDEX idx_kc_tags ON knowledge_card USING GIN (tags)",
    "CREATE INDEX idx_kc_embedding ON knowledge_card "
    "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)",
    # MC-010 RLS（migration 7b2dc371f434 同步）
    "ALTER TABLE employee ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY employee_tenant_isolation ON employee "
    "USING (tenant_id::text = current_setting('app.tenant_id', true))",
    "ALTER TABLE conversation ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY conversation_tenant_isolation ON conversation "
    "USING (tenant_id::text = current_setting('app.tenant_id', true))",
    # MC-005 + MC-006 RLS + unique partial index（migration 89c67361deb1 同步）
    "CREATE UNIQUE INDEX idx_skill_tenant_slug ON skill "
    "(COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid), slug)",
    "ALTER TABLE skill ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY skill_tenant_isolation ON skill USING ("
    "tenant_id IS NULL OR "
    "tenant_id::text = current_setting('app.tenant_id', true))",
    "ALTER TABLE skill_version ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY skill_version_tenant_isolation ON skill_version USING ("
    "tenant_id IS NULL OR "
    "tenant_id::text = current_setting('app.tenant_id', true))",
    "ALTER TABLE skill_binding ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY skill_binding_tenant_isolation ON skill_binding USING ("
    "tenant_id::text = current_setting('app.tenant_id', true))",
    "CREATE UNIQUE INDEX idx_tool_tenant_slug ON tool "
    "(COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid), slug)",
    "CREATE INDEX idx_tool_type ON tool (tool_type, enabled)",
    "ALTER TABLE tool ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY tool_tenant_isolation ON tool USING ("
    "tenant_id IS NULL OR "
    "tenant_id::text = current_setting('app.tenant_id', true))",
    "ALTER TABLE tool_invocation ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY tool_invocation_tenant_isolation ON tool_invocation USING ("
    "tenant_id::text = current_setting('app.tenant_id', true))",
    "ALTER TABLE tool_policy ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY tool_policy_tenant_isolation ON tool_policy USING ("
    "tenant_id IS NULL OR "
    "tenant_id::text = current_setting('app.tenant_id', true))",
    # MC-011 Channel Gateway RLS（migration 71c271e944a4 同步）
    "ALTER TABLE channel_binding ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY channel_binding_allow_all ON channel_binding USING (true)",
    "ALTER TABLE webhook_event ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY webhook_event_allow_all ON webhook_event USING (true)",
    "ALTER TABLE outbound_message ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY outbound_message_tenant_isolation ON outbound_message "
    "USING (tenant_id::text = current_setting('app.tenant_id', true))",
    # tenant_setting (migration 7bd48e428868)
    "ALTER TABLE tenant_setting ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY tenant_setting_tenant_isolation ON tenant_setting "
    "USING (tenant_id::text = current_setting('app.tenant_id', true))",
    # test_case / test_run (migration 9575402d6485)
    "ALTER TABLE test_case ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY test_case_tenant_isolation ON test_case "
    "USING (tenant_id::text = current_setting('app.tenant_id', true))",
    "ALTER TABLE test_run ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY test_run_tenant_isolation ON test_run "
    "USING (tenant_id::text = current_setting('app.tenant_id', true))",
]


# message 表必須是 partitioned，create_all 不認得；需手動重建
_MESSAGE_PARTITION_SQL = [
    "DROP TABLE IF EXISTS message CASCADE",
    """
    CREATE TABLE message (
        id UUID NOT NULL DEFAULT gen_random_uuid(),
        conversation_id UUID NOT NULL,
        seq INT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        content_raw_ref UUID,
        skill_invocation_id UUID,
        tool_invocations JSONB NOT NULL DEFAULT '[]',
        token_count INT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (id, created_at),
        UNIQUE (conversation_id, seq, created_at),
        CONSTRAINT ck_message_role_check CHECK (
            role IN ('user', 'assistant', 'tool', 'system')
        )
    ) PARTITION BY RANGE (created_at)
    """,
    # 建 2026 全年 partition（測試足用）
    *[
        f"CREATE TABLE message_2026_{m:02d} PARTITION OF message "
        f"FOR VALUES FROM ('2026-{m:02d}-01') TO "
        f"('2026-{m + 1:02d}-01')"
        for m in range(5, 12)
    ],
    "CREATE TABLE message_2026_12 PARTITION OF message "
    "FOR VALUES FROM ('2026-12-01') TO ('2027-01-01')",
    "ALTER TABLE message ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY message_allow_all ON message USING (true)",
    "ALTER TABLE conversation_handoff ENABLE ROW LEVEL SECURITY",
    "CREATE POLICY conversation_handoff_allow_all ON conversation_handoff USING (true)",
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
        # message 表 create_all 後重建為 partitioned
        for stmt in _MESSAGE_PARTITION_SQL:
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
