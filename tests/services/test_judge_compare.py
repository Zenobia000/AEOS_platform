"""LLMJudge ↔ KeywordJudge AB compare framework tests (Phase 1 後續 #17)."""

from __future__ import annotations

from typing import Any

from app.llm.client import LLMClient, LLMResponse, LLMUsage
from app.services.judge_compare import (
    compare_judges,
    format_compare_report,
)
from app.services.test_judge import KeywordJudge, LLMJudge


class _FakeLLM(LLMClient):
    def __init__(self, response: str) -> None:
        self.response = response

    async def complete(self, **kwargs: Any) -> LLMResponse:
        return LLMResponse(
            text=self.response,
            usage=LLMUsage(input_tokens=20, output_tokens=10),
        )


CASES = [
    {
        "name": "case_pass_both",
        "user_input": "請問退貨期限",
        "expected_outcome": "7 天",
        "expected_keywords": ["7 天"],
        "actual_output": "您好，本店退貨可於 7 天內辦理",
    },
    {
        "name": "case_fail_both",
        "user_input": "X",
        "expected_outcome": "Y",
        "expected_keywords": ["matterhorn"],  # 不會命中
        "actual_output": "irrelevant response",
    },
]


async def test_compare_agreement_all_agree() -> None:
    """LLM judge 回 'pass' → 兩個 judge 對第一題 agree。"""
    llm = LLMJudge(
        llm=_FakeLLM('{"score": 0.95, "reason": "all good"}'),
        pass_threshold=0.5,
    )
    report = await compare_judges(cases=CASES, llm_judge=llm)
    # case_pass_both: keyword passed (has '7 天'); llm passed (0.95 > 0.5) → agree
    # case_fail_both: keyword failed (no match); llm passed (0.95 > 0.5) → disagree
    assert report.total == 2
    assert report.disagreed == 1


async def test_compare_agreement_keyword_fallback() -> None:
    """LLM 回壞 JSON → fallback to keyword → 全 agree（fallback 等同 keyword）。"""
    llm = LLMJudge(
        llm=_FakeLLM("bad-json-not-a-dict"),
        pass_threshold=0.5,
        keyword_fallback_on_error=True,
    )
    report = await compare_judges(cases=CASES, llm_judge=llm)
    assert report.agreement_rate == 1.0  # fallback to keyword → 全相同


def test_format_compare_report_disagreement_lines() -> None:
    """format report 應列出 disagreement 細節。"""
    from app.services.judge_compare import CompareItem, CompareReport
    from app.services.test_judge import JudgeResult

    item = CompareItem(
        case_name="X",
        keyword_result=JudgeResult(status="failed", score=0.0, reason="no kw"),
        llm_result=JudgeResult(status="passed", score=0.9, reason="ok"),
        agreed=False,
    )
    report = CompareReport(
        total=1,
        agreed=0,
        disagreed=1,
        agreement_rate=0.0,
        items=[item],
    )
    out = format_compare_report(report)
    assert "1 agreed / 1 disagreed" in out or "0 agreed / 1 disagreed" in out
    assert "X" in out
    assert "Disagreements" in out


def test_disagreement_rate_property() -> None:
    from app.services.judge_compare import CompareReport

    r = CompareReport(total=10, agreed=7, disagreed=3, agreement_rate=0.7, items=[])
    assert r.disagreement_rate == 0.3


async def test_compare_empty_cases() -> None:
    llm = LLMJudge(
        llm=_FakeLLM('{"score": 1.0, "reason": "x"}'),
        pass_threshold=0.5,
    )
    report = await compare_judges(cases=[], llm_judge=llm)
    assert report.total == 0
    assert report.agreement_rate == 1.0


async def test_compare_uses_keyword_judge_default() -> None:
    """不傳 keyword_judge → 用 default KeywordJudge."""
    llm = LLMJudge(
        llm=_FakeLLM('{"score": 1.0, "reason": "ok"}'),
        pass_threshold=0.5,
    )
    report = await compare_judges(cases=CASES, keyword_judge=KeywordJudge(), llm_judge=llm)
    assert report.total == 2
