"""Seed demo data — 一鍵把 Expert Console 3 個 tab 都餵飽.

執行：
    uv run python -m scripts.seed_demo

產出：
- 1 個 tenant (slug='demo-tenant')
- 1 個 employee + channel_binding (line)
- 1 個 conversation + user message + 1 個 awaiting_review outbound（餵 Drafts tab）
- 3 張 draft KC（餵 KC tab）
- 5 個 test_case（餵 TestSet tab）

冪等：以 slug='demo-tenant' 為自然鍵；已存在則略過建 tenant，其它資源
也用 select-or-insert 模式避免重複。重跑安全。

跑完印出可貼到 Expert UI 的 tenant_id（含 localStorage key 提示）。
"""

from __future__ import annotations

import asyncio
import sys
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.channel_binding import ChannelBinding
from app.db.models.conversation import Conversation
from app.db.models.employee import Employee
from app.db.models.knowledge_card import KnowledgeCard
from app.db.models.outbound_message import OutboundMessage
from app.db.models.tenant import Tenant
from app.db.models.test_case import TestCase
from app.db.session import session_scope

DEMO_SLUG = "demo-tenant"
DEMO_CHANNEL_USER = "U-demo-end-user"
# 固定 UUID 讓 e2e 測試可以 hardcode 不必動態查
DEMO_TENANT_UUID = uuid.UUID("9e7ffb09-4f53-475a-a771-29b02f04906a")

KC_SEEDS: list[dict[str, list[str] | str]] = [
    {
        "card_type": "policy",
        "title": "退貨政策",
        "body_markdown": (
            "本店退貨可於到貨後 7 天內申請；請保留發票與包裝完整。"
            "退貨運費由買家負擔，除非商品瑕疵。"
        ),
        "tags": ["退貨", "政策", "發票"],
    },
    {
        "card_type": "faq",
        "title": "保固期限",
        "body_markdown": "全產品自購買日起享 1 年原廠保固，需出示購買證明。",
        "tags": ["保固", "1 年"],
    },
    {
        "card_type": "procedure",
        "title": "退款流程",
        "body_markdown": (
            "1. 申請退貨並寄回商品\n"
            "2. 收到並驗收後 3 個工作天內退款入帳\n"
            "3. 退款方式同付款方式（信用卡/匯款）"
        ),
        "tags": ["退款", "流程"],
    },
]

TEST_CASE_SEEDS: list[dict[str, list[str] | str]] = [
    {
        "name": "退貨期限",
        "user_input": "退貨多久內可以辦",
        "expected_outcome": "回答 7 天 + 須保留發票",
        "expected_keywords": ["7 天", "退貨", "發票"],
    },
    {
        "name": "保固",
        "user_input": "保固多久",
        "expected_outcome": "1 年原廠保固",
        "expected_keywords": ["1 年", "保固"],
    },
    {
        "name": "退款入帳",
        "user_input": "退款多久會收到",
        "expected_outcome": "3 個工作天內入帳",
        "expected_keywords": ["3 個工作天", "退款"],
    },
    {
        "name": "退貨運費",
        "user_input": "退貨運費誰出",
        "expected_outcome": "買家負擔，瑕疵除外",
        "expected_keywords": ["買家", "運費"],
    },
    {
        "name": "保固證明",
        "user_input": "保固需要什麼",
        "expected_outcome": "需出示購買證明",
        "expected_keywords": ["購買證明"],
    },
]

DEMO_DRAFT_TEXT = (
    "您好，本店退貨可於到貨後 7 天內申請，請保留發票與包裝；退款於收件驗收後 3 個工作天內入帳。"
)


async def _get_or_create_tenant(session: AsyncSession) -> Tenant:
    existing = (
        await session.execute(select(Tenant).where(Tenant.slug == DEMO_SLUG))
    ).scalar_one_or_none()
    if existing:
        print(f"[skip] tenant '{DEMO_SLUG}' already exists: id={existing.id}")
        return existing

    tenant = Tenant(id=DEMO_TENANT_UUID, name="Demo Co", slug=DEMO_SLUG)
    session.add(tenant)
    await session.flush()
    print(f"[ok] tenant created: id={tenant.id}")
    return tenant


async def _get_or_create_employee(session: AsyncSession, tenant: Tenant) -> Employee:
    existing = (
        await session.execute(select(Employee).where(Employee.tenant_id == tenant.id))
    ).scalar_one_or_none()
    if existing:
        print(f"[skip] employee already exists: id={existing.id}")
        return existing

    emp = Employee(
        tenant_id=tenant.id,
        name="Demo AI CS",
        role="customer_service",
        status="live",
        version="1.0.0",
    )
    session.add(emp)
    await session.flush()
    print(f"[ok] employee created: id={emp.id}")
    return emp


async def _get_or_create_channel_binding(
    session: AsyncSession, employee: Employee
) -> ChannelBinding:
    existing = (
        await session.execute(
            select(ChannelBinding).where(
                ChannelBinding.employee_id == employee.id,
                ChannelBinding.channel == "line",
            )
        )
    ).scalar_one_or_none()
    if existing:
        print(f"[skip] channel_binding (line) already exists: id={existing.id}")
        return existing

    cb = ChannelBinding(
        employee_id=employee.id,
        channel="line",
        config={
            "channel_id": "U-demo-line-channel",
            "channel_access_token": "demo-fake-token-do-not-use-in-prod",
            "channel_secret": "demo-secret",
        },
        enabled=True,
    )
    session.add(cb)
    await session.flush()
    print(f"[ok] channel_binding created: id={cb.id}")
    return cb


async def _seed_kc_drafts(session: AsyncSession, tenant: Tenant) -> int:
    """重複跑時不刪舊資料；用 title 為唯一識別."""
    existing_titles_rows = (
        await session.execute(
            select(KnowledgeCard.title).where(
                KnowledgeCard.tenant_id == tenant.id,
                KnowledgeCard.status == "draft",
            )
        )
    ).all()
    existing_titles = {row[0] for row in existing_titles_rows}

    inserted = 0
    for seed in KC_SEEDS:
        if seed["title"] in existing_titles:
            continue
        kc = KnowledgeCard(
            tenant_id=tenant.id,
            card_type=seed["card_type"],
            title=seed["title"],
            body_markdown=seed["body_markdown"],
            tags=list(seed["tags"]) if isinstance(seed["tags"], list) else [],
            status="draft",
        )
        session.add(kc)
        inserted += 1
    await session.flush()
    print(f"[ok] KC drafts inserted: {inserted} (existing skipped: {len(existing_titles)})")
    return inserted


async def _seed_test_cases(session: AsyncSession, tenant: Tenant) -> int:
    existing_names_rows = (
        await session.execute(select(TestCase.name).where(TestCase.tenant_id == tenant.id))
    ).all()
    existing_names = {row[0] for row in existing_names_rows}

    inserted = 0
    for seed in TEST_CASE_SEEDS:
        if seed["name"] in existing_names:
            continue
        tc = TestCase(
            tenant_id=tenant.id,
            name=seed["name"],
            user_input=seed["user_input"],
            expected_outcome=seed["expected_outcome"],
            expected_keywords=(
                list(seed["expected_keywords"])
                if isinstance(seed["expected_keywords"], list)
                else []
            ),
            created_by="seed-script",
        )
        session.add(tc)
        inserted += 1
    await session.flush()
    print(f"[ok] test_case inserted: {inserted} (existing skipped: {len(existing_names)})")
    return inserted


async def _seed_awaiting_review_draft(
    session: AsyncSession,
    tenant: Tenant,
    employee: Employee,
) -> None:
    """建一個 awaiting_review outbound 餵 Draft tab.

    需要：conversation + assistant message + outbound_message。
    若已存在（依 channel_user_id 唯一）就略過。
    """
    existing = (
        await session.execute(
            select(OutboundMessage).where(
                OutboundMessage.tenant_id == tenant.id,
                OutboundMessage.channel_user_id == DEMO_CHANNEL_USER,
                OutboundMessage.status == "awaiting_review",
            )
        )
    ).scalar_one_or_none()
    if existing:
        print(f"[skip] awaiting_review outbound already exists: id={existing.id}")
        return

    conv = Conversation(
        tenant_id=tenant.id,
        employee_id=employee.id,
        employee_version="1.0.0",
        end_user_pseudo_id="demo-pseudo-user",
        channel="line",
        channel_user_id=DEMO_CHANNEL_USER,
        status="active",
    )
    session.add(conv)
    await session.flush()

    # 寫 user message（seq=1）
    await session.execute(
        text(
            "INSERT INTO message "
            "(id, conversation_id, seq, role, content, created_at) "
            "VALUES (gen_random_uuid(), :cid, 1, 'user', :c, NOW())"
        ),
        {"cid": str(conv.id), "c": "請問退貨多久內可以辦？要帶什麼？"},
    )
    # 寫 assistant draft message（seq=2）
    msg_row = (
        await session.execute(
            text(
                "INSERT INTO message "
                "(id, conversation_id, seq, role, content, created_at) "
                "VALUES (gen_random_uuid(), :cid, 2, 'assistant', :c, NOW()) "
                "RETURNING id"
            ),
            {"cid": str(conv.id), "c": DEMO_DRAFT_TEXT},
        )
    ).first()
    msg_id = uuid.UUID(str(msg_row[0]))  # type: ignore[index]
    await session.execute(
        text("UPDATE conversation SET message_count = 2, last_message_at = NOW() WHERE id = :cid"),
        {"cid": str(conv.id)},
    )

    out = OutboundMessage(
        tenant_id=tenant.id,
        conversation_id=conv.id,
        message_id=msg_id,
        channel="line",
        channel_user_id=DEMO_CHANNEL_USER,
        status="awaiting_review",
    )
    session.add(out)
    await session.flush()
    print(f"[ok] awaiting_review outbound created: id={out.id}")


async def _reset_demo_tenant(session: AsyncSession) -> None:
    """刪掉 demo tenant + 所有相關資料。

    用於 e2e test 之間重置狀態。不是所有 FK 都 CASCADE（kc / ingestion
    等沒設），所以手動逐表清。Expert account 是跨 tenant 不刪。
    """
    from sqlalchemy import text

    existing = (
        await session.execute(select(Tenant).where(Tenant.slug == DEMO_SLUG))
    ).scalar_one_or_none()
    if existing is None:
        print(f"[skip] tenant '{DEMO_SLUG}' not present; nothing to reset")
        return

    tid = str(existing.id)

    # 依 FK 反向依賴順序逐表清
    # message 是 partitioned；手動 DELETE
    await session.execute(
        text(
            "DELETE FROM message WHERE conversation_id IN "
            "(SELECT id FROM conversation WHERE tenant_id = :tid)"
        ),
        {"tid": tid},
    )
    # 與 conversation 相關的（outbound 走 conversation FK）
    await session.execute(
        text("DELETE FROM outbound_message WHERE tenant_id = :tid"),
        {"tid": tid},
    )
    await session.execute(
        text(
            "DELETE FROM conversation_handoff "
            "WHERE from_conversation_id IN "
            "(SELECT id FROM conversation WHERE tenant_id = :tid)"
        ),
        {"tid": tid},
    )
    await session.execute(
        text("DELETE FROM conversation WHERE tenant_id = :tid"),
        {"tid": tid},
    )
    # test_run_case 沒 tenant_id；走 FK 到 test_run
    await session.execute(
        text(
            "DELETE FROM test_run_case "
            "WHERE test_run_id IN (SELECT id FROM test_run WHERE tenant_id = :tid)"
        ),
        {"tid": tid},
    )
    # KB / TestSet / Tool / Skill / 其他 per-tenant 表
    # 不刪 audit_log（append-only trigger 保護；歷史紀錄保留）
    # 順序：skill_binding → skill_version → skill (FK chain)
    for table in (
        "knowledge_card",
        "ingestion_job",
        "test_run",
        "test_case",
        "tool_invocation",
        "skill_binding",
        "skill_version",  # CR-0002: sync_from_git 產生
        "skill",  # CR-0002: sync_from_git 產生
        "tenant_setting",
        "api_key",
    ):
        await session.execute(
            text(f"DELETE FROM {table} WHERE tenant_id = :tid"),
            {"tid": tid},
        )
    # channel_binding 走 employee FK
    await session.execute(
        text(
            "DELETE FROM channel_binding "
            "WHERE employee_id IN (SELECT id FROM employee WHERE tenant_id = :tid)"
        ),
        {"tid": tid},
    )
    await session.execute(
        text("DELETE FROM employee WHERE tenant_id = :tid"),
        {"tid": tid},
    )
    await session.delete(existing)
    await session.flush()
    print(f"[reset] deleted tenant '{DEMO_SLUG}' + 所有相關資料 (id={tid})")


async def _seed_6_vertical_skills(
    session: AsyncSession,
    tenant: Tenant,
    employee: Employee,
) -> None:
    """Phase 1 後續 #1：seed_demo 擴成 6 vertical（customer-service / hr / it-helpdesk /
    sales / finance / legal）。

    流程：
    1. 呼叫 SkillRegistryService.sync_from_git 掃 skills/ → upsert skill / skill_version
    2. 為 employee 建 6 個 skill_binding（customer-service 設 is_default=true）
    3. routing_rule：每 vertical 用 keyword fast path（精選 vertical 關鍵字）
    """
    from pathlib import Path

    from sqlalchemy import select as _select

    from app.db.models.skill import Skill
    from app.db.models.skill_binding import SkillBinding
    from app.db.models.skill_version import SkillVersion
    from app.services import skill_registry as _sr

    repo_root = Path(__file__).resolve().parents[1]
    result = await _sr.sync_from_git(session, tenant_id=tenant.id, skills_root=repo_root / "skills")
    print(
        f"[ok] skill sync: +{result.skills_inserted} skill / "
        f"+{result.versions_inserted} version / "
        f"errors={len(result.errors)}"
    )

    # routing_rule keyword 精選表
    routing_table: dict[str, dict[str, object]] = {
        "customer-service/faq-respond": {
            "is_default": True,
            "rule": {},
        },
        "hr/leave-request": {
            "is_default": False,
            "rule": {
                "type": "keyword",
                "params": {"keywords": ["請假", "leave", "事假", "年假", "病假", "婚假"]},
                "priority": 10,
            },
        },
        "it-helpdesk/password-reset": {
            "is_default": False,
            "rule": {
                "type": "keyword",
                "params": {
                    "keywords": [
                        "密碼",
                        "password",
                        "登入",
                        "帳號鎖",
                        "MFA",
                        "SSO",
                    ]
                },
                "priority": 10,
            },
        },
        "sales/quote-request": {
            "is_default": False,
            "rule": {
                "type": "keyword",
                "params": {"keywords": ["報價", "quote", "方案", "試用", "pricing"]},
                "priority": 10,
            },
        },
        "finance/expense-claim": {
            "is_default": False,
            "rule": {
                "type": "keyword",
                "params": {"keywords": ["報帳", "差旅", "發票", "費用", "額度"]},
                "priority": 10,
            },
        },
        "legal/contract-review": {
            "is_default": False,
            "rule": {
                "type": "keyword",
                "params": {"keywords": ["合約", "NDA", "MSA", "條款", "違約金"]},
                "priority": 10,
            },
        },
    }

    bindings_added = 0
    for slug, cfg in routing_table.items():
        # 找對應 skill_version
        sv_row = (
            await session.execute(
                _select(SkillVersion)
                .join(Skill, SkillVersion.skill_id == Skill.id)
                .where(Skill.tenant_id == tenant.id, Skill.slug == slug)
            )
        ).scalar_one_or_none()
        if sv_row is None:
            print(f"[warn] no skill_version for {slug}; skipped binding")
            continue

        # 已存在則 skip
        existing = (
            await session.execute(
                _select(SkillBinding).where(
                    SkillBinding.employee_id == employee.id,
                    SkillBinding.skill_version_id == sv_row.id,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue

        session.add(
            SkillBinding(
                tenant_id=tenant.id,
                employee_id=employee.id,
                skill_version_id=sv_row.id,
                routing_rule=cfg["rule"],  # type: ignore[arg-type]
                is_default=bool(cfg["is_default"]),
                priority=0 if cfg["is_default"] else 10,
            )
        )
        bindings_added += 1
    await session.flush()
    print(f"[ok] skill_binding +{bindings_added} (6 vertical for demo employee)")


async def main() -> None:
    reset = "--reset" in sys.argv

    if reset:
        async with session_scope() as session:
            await _reset_demo_tenant(session)

    async with session_scope() as session:
        tenant = await _get_or_create_tenant(session)
        employee = await _get_or_create_employee(session, tenant)
        await _get_or_create_channel_binding(session, employee)
        await _seed_kc_drafts(session, tenant)
        await _seed_test_cases(session, tenant)
        await _seed_awaiting_review_draft(session, tenant, employee)
        await _seed_6_vertical_skills(session, tenant, employee)

    print()
    print("=" * 60)
    print(f"DEMO TENANT ID: {tenant.id}")
    print()
    print("→ Expert UI: open http://localhost:5173")
    print("  - Drafts tab：應看到 1 筆退貨 draft 等審")
    print(f"  - KC tab：應看到 {len(KC_SEEDS)} 張 draft KC")
    print("  - TestSet tab：在 Tenant ID 欄貼上：")
    print(f"      {tenant.id}")
    print(
        f"    （或在瀏覽器 console: localStorage.setItem('aeos.testset.tenant_id', '{tenant.id}')）"
    )
    print(f"    然後重新整理，應看到 {len(TEST_CASE_SEEDS)} 個 test cases")
    print()
    print("→ Admin API（kill switch）：")
    print(f"  curl http://localhost:8000/api/v1/admin/kill-switch/{tenant.id}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
