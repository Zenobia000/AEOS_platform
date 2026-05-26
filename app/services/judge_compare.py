"""LLMJudge ↔ KeywordJudge AB compare framework (Phase 1 後續 #17).

對應 PRD-001 §AC-001 + ADR-0010：當 pilot 真實對話進來後，要評估 LLM-based judge
與 simple keyword judge 的 disagreement → 進而決定 production judge 策略。

Phase 1 framework only：跑一輪 compare 印出 disagreement matrix；不自動切換 production judge。
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.test_judge import (
    Judge,
    JudgeResult,
    KeywordJudge,
)


@dataclass(frozen=True)
class CompareItem:
    """單一 case 在兩個 judge 下的結果。"""

    case_name: str
    keyword_result: JudgeResult
    llm_result: JudgeResult
    agreed: bool


@dataclass(frozen=True)
class CompareReport:
    """整個 test_set 的 AB 比較摘要。"""

    total: int
    agreed: int
    disagreed: int
    agreement_rate: float
    items: list[CompareItem]

    @property
    def disagreement_rate(self) -> float:
        return self.disagreed / self.total if self.total else 0.0


async def compare_judges(
    *,
    cases: list[dict[str, object]],
    keyword_judge: Judge | None = None,
    llm_judge: Judge,
) -> CompareReport:
    """跑同一 test_set 透過兩個 judge → 算 agreement / disagreement。

    Args:
        cases: 每個 case dict 含 name/user_input/expected_outcome/expected_keywords/actual_output
        keyword_judge: 預設用 KeywordJudge()
        llm_judge: LLMJudge 必須注入（含 LLMClient）

    Returns:
        CompareReport — 含 agreement_rate + 每個 case 的雙 judge 結果
    """
    kw = keyword_judge or KeywordJudge()

    items: list[CompareItem] = []
    for case in cases:
        kw_result = await kw.evaluate(
            user_input=str(case["user_input"]),
            expected_outcome=str(case["expected_outcome"]),
            expected_keywords=list(case["expected_keywords"]),  # type: ignore[arg-type]
            actual_output=str(case["actual_output"]),
        )
        llm_result = await llm_judge.evaluate(
            user_input=str(case["user_input"]),
            expected_outcome=str(case["expected_outcome"]),
            expected_keywords=list(case["expected_keywords"]),  # type: ignore[arg-type]
            actual_output=str(case["actual_output"]),
        )
        agreed = kw_result.status == llm_result.status
        items.append(
            CompareItem(
                case_name=str(case["name"]),
                keyword_result=kw_result,
                llm_result=llm_result,
                agreed=agreed,
            )
        )

    total = len(items)
    agreed_count = sum(1 for i in items if i.agreed)
    return CompareReport(
        total=total,
        agreed=agreed_count,
        disagreed=total - agreed_count,
        agreement_rate=(agreed_count / total) if total else 1.0,
        items=items,
    )


def format_compare_report(report: CompareReport) -> str:
    """人類可讀格式（給 CLI / log）。"""
    lines = [
        f"AB compare: {report.agreed} agreed / {report.disagreed} disagreed "
        f"/ {report.total} total → agreement_rate = {report.agreement_rate:.1%}",
        "",
        "Disagreements:",
    ]
    for item in report.items:
        if not item.agreed:
            lines.append(
                f"  - {item.case_name}: keyword={item.keyword_result.status} "
                f"(score {item.keyword_result.score:.2f}) "
                f"vs llm={item.llm_result.status} (score {item.llm_result.score:.2f})"
            )
    return "\n".join(lines)
