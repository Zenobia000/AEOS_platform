"""Async SQLAlchemy session + RLS context.

依 ADR-0007（multi-tenant 共享 PG + RLS + 應用層雙重檢查）：
- 每個 async session 對應一個 request
- 進入 request 時呼叫 `set_tenant_context(session, tenant_id)`，
  會 SET LOCAL app.tenant_id = <id>；PG RLS policy 用此 GUC
  決定 row visibility
- session 結束時 GUC 隨 transaction 自動釋放

usage:
    async with session_scope(tenant_id=...) as session:
        result = await session.execute(...)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Lazy-init engine。第一次呼叫時建。"""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.app_env == "dev",
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Lazy-init sessionmaker。"""
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            autoflush=False,
            class_=AsyncSession,
        )
    return _sessionmaker


async def set_tenant_context(session: AsyncSession, tenant_id: str) -> None:
    """注入 RLS 用的 tenant_id GUC。

    PG RLS policy 形如：
        CREATE POLICY tenant_isolation ON some_table
            USING (tenant_id = current_setting('app.tenant_id')::uuid);

    依 SEC-001 §6.1 #4 需配 cross-tenant query 測試（TC-SEC-001）。
    """
    # NOTE: SET LOCAL 不支援 bind parameter；改用 set_config(name, value, is_local)
    # is_local = true → 只在 transaction 內生效（等價 SET LOCAL）
    from sqlalchemy import text

    await session.execute(
        text("SELECT set_config('app.tenant_id', :tid, true)"),
        {"tid": tenant_id},
    )


@asynccontextmanager
async def session_scope(
    tenant_id: str | None = None,
) -> AsyncIterator[AsyncSession]:
    """產生一個 async session；可選注入 RLS tenant_id。

    Args:
        tenant_id: 若提供，在 transaction 開頭注入 RLS context；
                   admin / system 動作可省略（但對應的查詢需走 BYPASSRLS 角色）

    Yields:
        AsyncSession（commit / rollback 自動處理）
    """
    sm = get_sessionmaker()
    async with sm() as session:
        try:
            await session.begin()
            if tenant_id is not None:
                await set_tenant_context(session, tenant_id)
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """關閉 engine 連線池（FastAPI shutdown 用）。"""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
