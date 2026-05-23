"""TestRunner — 跑一個 test_run 的所有 cases (S3 / AC-001).

設計：
- 每個 case 用一個 LLMClient.complete() one-shot 呼叫（不走 DraftProcessor，
  避免污染 conversation / message 表；test_run 是離線品質驗證）
- judge 透過 Judge 介面注入（KeywordJudge / LLMJudge 可換）
- 失敗也算進 failed_count；exception 進 status='error'

對應 PRD-001 §5.2 F-TS-02 + AC-001 §pass rate ≥ 0.80 measurement。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.test_case import TestCase
from app.db.models.test_run_case import TestRunCase
from app.llm.client import LLMClient, LLMMessage
from app.services import test_set
from app.services.test_judge import (
    DEFAULT_PASS_THRESHOLD,
    Judge,
    KeywordJudge,
)
from app.skill import SkillLoader


@dataclass(frozen=True)
class TestRunResult:
    run_id: uuid.UUID
    total: int
    passed: int
    failed: int
    errored: int
    pass_rate: float


class TestSetRunner:
    """跑單一 test_run。

    Args:
        llm: LLMClient — 跑 skill 的對話用
        skill_loader: 取 system prompt
        judge: 評分策略 (KeywordJudge / LLMJudge)；None 預設 KeywordJudge
            搭配 pass_threshold（向後相容）
        pass_threshold: 預設 KeywordJudge 的 threshold（judge 已傳則忽略）
    """

    __test__ = False  # 阻止 pytest 把這個 class 當測試類別收集

    def __init__(
        self,
        *,
        llm: LLMClient,
        skill_loader: SkillLoader,
        judge: Judge | None = None,
        pass_threshold: float = DEFAULT_PASS_THRESHOLD,
    ) -> None:
        self._llm = llm
        self._skill_loader = skill_loader
        self._judge: Judge = judge or KeywordJudge(pass_threshold=pass_threshold)

    async def run(
        self,
        session: AsyncSession,
        *,
        run_id: uuid.UUID,
    ) -> TestRunResult:
        run = await test_set.mark_run_running(session, run_id=run_id)
        skill = self._skill_loader.load(run.skill_slug, run.skill_version)

        # 撈所有 pending case 對 (test_run_case + test_case 內容)
        rows = (
            await session.execute(
                select(TestRunCase, TestCase)
                .join(TestCase, TestRunCase.test_case_id == TestCase.id)
                .where(TestRunCase.test_run_id == run_id)
                .where(TestRunCase.status == "pending")
            )
        ).all()

        passed = 0
        failed = 0
        errored = 0

        for trc, tc in rows:
            try:
                response = await self._llm.complete(
                    messages=[LLMMessage(role="user", content=tc.user_input)],
                    system=skill.system_prompt,
                    max_tokens=512,
                    temperature=0.0,
                )
                judgement = await self._judge.evaluate(
                    user_input=tc.user_input,
                    expected_outcome=tc.expected_outcome,
                    expected_keywords=list(tc.expected_keywords),
                    actual_output=response.text,
                )
                trc.status = judgement.status
                trc.actual_output = response.text
                trc.judge_score = judgement.score
                trc.judge_reason = judgement.reason
                trc.executed_at = datetime.now(UTC)
                if judgement.status == "passed":
                    passed += 1
                else:
                    failed += 1
            except Exception as exc:
                trc.status = "error"
                trc.judge_reason = f"runner exception: {exc!s}"[:500]
                trc.executed_at = datetime.now(UTC)
                errored += 1
            await session.flush()

        summary = await test_set.finalize_run(session, run_id=run_id)
        return TestRunResult(
            run_id=run.id,
            total=summary.total_cases,
            passed=passed,
            failed=failed,
            errored=errored,
            pass_rate=summary.pass_rate,
        )
