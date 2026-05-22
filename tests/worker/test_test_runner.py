"""TestRunner integration test — fake LLM + 真實 DB + judge."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.tenant import Tenant
from app.db.models.test_run_case import TestRunCase
from app.llm.client import LLMClient, LLMResponse, LLMUsage
from app.services import test_set
from app.skill import SkillLoader
from app.worker.test_runner import TestSetRunner


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class _StubLLM(LLMClient):
    """根據 user_input 內容回傳固定 answer（測試用）."""

    def __init__(self, answers_by_input: dict[str, str]) -> None:
        self._answers = answers_by_input

    async def complete(self, **kwargs: Any) -> LLMResponse:
        messages = kwargs["messages"]
        last_user = messages[-1].content
        text = self._answers.get(last_user, "我不知道")
        return LLMResponse(
            text=text,
            tool_uses=[],
            stop_reason="end_turn",
            usage=LLMUsage(input_tokens=10, output_tokens=20),
            model="stub",
        )


async def _seed_tenant(session: AsyncSession, suffix: str = "tr") -> Tenant:
    t = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}-{suffix}")
    session.add(t)
    await session.flush()
    return t


async def test_runner_executes_cases_and_aggregates(
    db_session: AsyncSession,
) -> None:
    tenant = await _seed_tenant(db_session, "exec")
    await test_set.create_test_case(
        db_session,
        tenant_id=tenant.id,
        name="退貨期限",
        user_input="退貨多久",
        expected_outcome="7 天",
        expected_keywords=["7 天", "退貨"],
    )
    await test_set.create_test_case(
        db_session,
        tenant_id=tenant.id,
        name="保固",
        user_input="保固期",
        expected_outcome="1 年",
        expected_keywords=["1 年", "保固"],
    )
    # 第三題我們刻意讓 LLM 答錯
    await test_set.create_test_case(
        db_session,
        tenant_id=tenant.id,
        name="退款",
        user_input="退款流程",
        expected_outcome="3 個工作天內入帳",
        expected_keywords=["3 個工作天", "入帳"],
    )

    run = await test_set.create_test_run(
        db_session,
        tenant_id=tenant.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )

    llm = _StubLLM(
        answers_by_input={
            "退貨多久": "您好，退貨可於 7 天內處理",
            "保固期": "本店保固 1 年",
            "退款流程": "請聯絡客服",  # 不會包含 expected keywords → fail
        }
    )
    runner = TestSetRunner(
        llm=llm,
        skill_loader=SkillLoader(root=_repo_root() / "skills"),
    )
    result = await runner.run(db_session, run_id=run.id)

    assert result.total == 3
    assert result.passed == 2
    assert result.failed == 1
    assert abs(result.pass_rate - 2 / 3) < 0.01

    trcs = (
        (await db_session.execute(select(TestRunCase).where(TestRunCase.test_run_id == run.id)))
        .scalars()
        .all()
    )
    statuses = sorted([t.status for t in trcs])
    assert statuses == ["failed", "passed", "passed"]


class _ExplosiveLLM(LLMClient):
    async def complete(self, **kwargs: Any) -> LLMResponse:
        raise RuntimeError("LLM API down")


async def test_runner_marks_error_on_llm_exception(
    db_session: AsyncSession,
) -> None:
    tenant = await _seed_tenant(db_session, "explode")
    await test_set.create_test_case(
        db_session,
        tenant_id=tenant.id,
        name="x",
        user_input="anything",
        expected_outcome="y",
        expected_keywords=["z"],
    )
    run = await test_set.create_test_run(
        db_session,
        tenant_id=tenant.id,
        skill_slug="customer-service/faq-respond",
        skill_version="v1.0.0",
    )
    runner = TestSetRunner(
        llm=_ExplosiveLLM(),
        skill_loader=SkillLoader(root=_repo_root() / "skills"),
    )
    result = await runner.run(db_session, run_id=run.id)
    assert result.errored == 1
    assert result.passed == 0
    assert result.pass_rate == 0.0

    trcs = (
        (await db_session.execute(select(TestRunCase).where(TestRunCase.test_run_id == run.id)))
        .scalars()
        .all()
    )
    assert trcs[0].status == "error"
    assert "LLM API down" in (trcs[0].judge_reason or "")
