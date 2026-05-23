"""MC-010 Conversation Engine 測試 — employee / conversation / message / handoff."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.conversation import Conversation
from app.db.models.conversation_handoff import ConversationHandoff
from app.db.models.employee import Employee
from app.db.models.tenant import Tenant


async def _make_tenant(session: AsyncSession, slug: str) -> Tenant:
    t = Tenant(name=f"Tenant-{slug}", slug=slug)
    session.add(t)
    await session.flush()
    return t


async def _make_employee(session: AsyncSession, tenant: Tenant) -> Employee:
    e = Employee(
        tenant_id=tenant.id,
        name="AI 客服",
        role="customer_service",
        status="draft",
        version="1.0.0",
    )
    session.add(e)
    await session.flush()
    return e


# ── Employee ─────────────────────────────────────────


async def test_employee_create(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "emp-create")
    emp = await _make_employee(db_session, tenant)

    assert emp.id is not None
    assert emp.persona_config == {}
    assert emp.runtime_snapshot == {}


async def test_employee_invalid_status(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "emp-bad-status")
    e = Employee(
        tenant_id=tenant.id,
        name="bad",
        role="customer_service",
        status="invalid",
        version="1.0.0",
    )
    db_session.add(e)
    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()
    assert "status_check" in str(exc.value).lower()


async def test_employee_runtime_snapshot_jsonb(db_session: AsyncSession) -> None:
    """runtime_snapshot 是 Frozen Runtime 的具體實作 — 任意 JSONB 結構。"""
    tenant = await _make_tenant(db_session, "emp-snap")
    snapshot = {
        "skill_bindings": [{"skill_id": "x", "version": "1.0.0"}],
        "tool_bindings": ["knowledge_search", "ticket_create"],
        "llm_config": {"model": "claude-sonnet-4-6", "temperature": 0.3},
    }
    e = Employee(
        tenant_id=tenant.id,
        name="frozen",
        role="customer_service",
        status="live",
        version="2.1.0",
        runtime_snapshot=snapshot,
    )
    db_session.add(e)
    await db_session.flush()

    fetched = (await db_session.execute(select(Employee).where(Employee.id == e.id))).scalar_one()
    assert fetched.runtime_snapshot == snapshot


# ── Conversation ─────────────────────────────────────


async def test_conversation_create_with_defaults(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "conv-create")
    emp = await _make_employee(db_session, tenant)
    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=emp.id,
        employee_version="1.0.0",
        end_user_pseudo_id="pseudo-user-xyz",
        channel="line",
        channel_user_id="line-uid-hash",
    )
    db_session.add(conv)
    await db_session.flush()

    assert conv.id is not None
    assert conv.status == "open"
    assert conv.message_count == 0
    assert conv.started_at is not None
    assert conv.convo_metadata == {}


async def test_conversation_channel_check(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "conv-bad-chan")
    emp = await _make_employee(db_session, tenant)
    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=emp.id,
        employee_version="1.0.0",
        end_user_pseudo_id="x",
        channel="wechat",  # 不在允許清單
        channel_user_id="x",
    )
    db_session.add(conv)
    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()
    assert "channel_check" in str(exc.value).lower()


async def test_conversation_outcome_check(db_session: AsyncSession) -> None:
    """outcome 可為 NULL 或 4 個允許值之一。"""
    tenant = await _make_tenant(db_session, "conv-outcome")
    emp = await _make_employee(db_session, tenant)
    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=emp.id,
        employee_version="1.0.0",
        end_user_pseudo_id="x",
        channel="line",
        channel_user_id="x",
        outcome="weird_outcome",
    )
    db_session.add(conv)
    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()
    assert "outcome_check" in str(exc.value).lower()


# ── Message（partition）─────────────────────────────


async def test_message_partition_routing(db_session: AsyncSession) -> None:
    """寫入 message 應自動路由到對應月份 partition。"""
    tenant = await _make_tenant(db_session, "msg-part")
    emp = await _make_employee(db_session, tenant)
    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=emp.id,
        employee_version="1.0.0",
        end_user_pseudo_id="u",
        channel="line",
        channel_user_id="u",
    )
    db_session.add(conv)
    await db_session.flush()

    # 直接 raw insert（避免 ORM model 對 partitioned table 的潛在問題）
    msg_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO message "
            "(id, conversation_id, seq, role, content, created_at) "
            "VALUES (:id, :cid, 1, 'user', 'hello', '2026-05-15T10:00:00+00')"
        ),
        {"id": str(msg_id), "cid": str(conv.id)},
    )

    # 從 message_2026_05 子分區查得到（partition pruning）
    result = await db_session.execute(
        text("SELECT id FROM message_2026_05 WHERE id = :id"),
        {"id": str(msg_id)},
    )
    assert result.scalar_one_or_none() == msg_id

    # 從 parent table 查也能取到
    result_parent = await db_session.execute(
        text("SELECT content FROM message WHERE id = :id"),
        {"id": str(msg_id)},
    )
    assert result_parent.scalar_one() == "hello"


async def test_message_role_check(db_session: AsyncSession) -> None:
    """role 必須是 4 個允許值之一."""
    tenant = await _make_tenant(db_session, "msg-role")
    emp = await _make_employee(db_session, tenant)
    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=emp.id,
        employee_version="1.0.0",
        end_user_pseudo_id="u",
        channel="line",
        channel_user_id="u",
    )
    db_session.add(conv)
    await db_session.flush()

    with pytest.raises(IntegrityError) as exc:
        await db_session.execute(
            text(
                "INSERT INTO message "
                "(id, conversation_id, seq, role, content, created_at) "
                "VALUES (gen_random_uuid(), :cid, 1, 'admin', 'x', "
                "'2026-05-15T10:00:00+00')"
            ),
            {"cid": str(conv.id)},
        )
    assert "role_check" in str(exc.value).lower()


async def test_message_partitions_exist(db_session: AsyncSession) -> None:
    """8 個月份 partition 應全部存在 (2026_05 ~ 2026_12)."""
    result = await db_session.execute(
        text(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname='public' AND tablename LIKE 'message_2026_%' "
            "ORDER BY tablename"
        )
    )
    names = [row[0] for row in result.all()]
    expected = [f"message_2026_{m:02d}" for m in range(5, 13)]
    assert names == expected


# ── ConversationHandoff ─────────────────────────────


async def test_handoff_create_pending(db_session: AsyncSession) -> None:
    """新 handoff（pending）— to_conversation_id 為 NULL."""
    tenant = await _make_tenant(db_session, "hand-pending")
    emp = await _make_employee(db_session, tenant)
    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=emp.id,
        employee_version="1.0.0",
        end_user_pseudo_id="u",
        channel="line",
        channel_user_id="u",
    )
    db_session.add(conv)
    await db_session.flush()

    handoff = ConversationHandoff(
        from_conversation_id=conv.id,
        reason="low_confidence",
        handoff_message="AI 不確定，請接手",
    )
    db_session.add(handoff)
    await db_session.flush()

    assert handoff.id is not None
    assert handoff.to_conversation_id is None
    assert handoff.picked_up_at is None


async def test_handoff_reason_check(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, "hand-bad")
    emp = await _make_employee(db_session, tenant)
    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=emp.id,
        employee_version="1.0.0",
        end_user_pseudo_id="u",
        channel="line",
        channel_user_id="u",
    )
    db_session.add(conv)
    await db_session.flush()

    h = ConversationHandoff(
        from_conversation_id=conv.id,
        reason="bored",  # 不在允許清單
    )
    db_session.add(h)
    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()
    assert "reason_check" in str(exc.value).lower()


# ── RLS Policies ────────────────────────────────────


async def test_mc010_rls_policies_exist(db_session: AsyncSession) -> None:
    """所有 MC-010 表都應有對應 RLS policy（除 message 是 ALL 允許）."""
    result = await db_session.execute(
        text(
            "SELECT tablename, policyname FROM pg_policies "
            "WHERE schemaname='public' "
            "AND tablename IN ('employee', 'conversation', "
            "'message', 'conversation_handoff')"
        )
    )
    policies = {(row[0], row[1]) for row in result.all()}
    assert ("employee", "employee_tenant_isolation") in policies
    assert ("conversation", "conversation_tenant_isolation") in policies
    assert ("message", "message_allow_all") in policies
    assert (
        "conversation_handoff",
        "conversation_handoff_allow_all",
    ) in policies
