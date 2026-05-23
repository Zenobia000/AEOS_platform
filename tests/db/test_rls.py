"""RLS policy & set_config 行為測試 — 對應 SEC-001 §6.1 #4 部分.

NOTE: 因 testcontainers 的 PG user 是 superuser + 表 owner，PostgreSQL
預設讓 owner BYPASSRLS（除非 FORCE）。完整 cross-tenant isolation 行為
測試需在 S2 後續任務建立 non-owner role 後補上。

本檔涵蓋：
- 3 個 RLS policy 確實已建（依 pg_policies 系統表）
- set_config('app.tenant_id', ..., true) 可正常設定 + 讀回（驗證 helper SQL）
- current_setting 對未設值的 GUC 不會 raise（policy 內 USING 用 missing_ok=true）
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def test_rls_policies_registered(db_session: AsyncSession) -> None:
    """三個 policy 應存在於 pg_policies。"""
    result = await db_session.execute(
        text(
            "SELECT tablename, policyname FROM pg_policies "
            "WHERE schemaname='public' "
            "ORDER BY tablename, policyname"
        )
    )
    policies = {(row[0], row[1]) for row in result.all()}
    assert ("tenant", "tenant_self_isolation") in policies
    assert ("api_key", "api_key_tenant_isolation") in policies
    assert ("audit_log", "audit_log_tenant_isolation") in policies


async def test_rls_enabled_on_tables(db_session: AsyncSession) -> None:
    """三張表都已 ENABLE ROW LEVEL SECURITY。"""
    result = await db_session.execute(
        text(
            "SELECT tablename, rowsecurity FROM pg_tables "
            "WHERE schemaname='public' "
            "AND tablename IN ('tenant', 'api_key', 'audit_log')"
        )
    )
    rls_map = {row[0]: row[1] for row in result.all()}
    assert rls_map["tenant"] is True
    assert rls_map["api_key"] is True
    assert rls_map["audit_log"] is True


async def test_set_config_local_works(db_session: AsyncSession) -> None:
    """set_config('app.tenant_id', :tid, true) 可寫入 + 讀回。"""
    expected = "11111111-2222-3333-4444-555555555555"
    await db_session.execute(
        text("SELECT set_config('app.tenant_id', :tid, true)"),
        {"tid": expected},
    )
    got = await db_session.execute(text("SELECT current_setting('app.tenant_id', true)"))
    assert got.scalar_one() == expected


async def test_current_setting_missing_returns_empty(db_session: AsyncSession) -> None:
    """未設過的 GUC + missing_ok=true → 回 empty string，不 raise."""
    got = await db_session.execute(text("SELECT current_setting('app.never_set', true)"))
    # PostgreSQL 對沒設過的 GUC + missing_ok=true 回 NULL（或 empty）
    val = got.scalar_one()
    assert val is None or val == ""
