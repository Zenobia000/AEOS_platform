"""Test judge — 判斷 AI 輸出是否符合預期 (S3 / AC-001).

Phase 1 採關鍵字白名單法（簡單可解釋）：
- 將 actual_output 與 expected_keywords 全部 lowercase 後對比
- score = matched_count / total_keywords（無關鍵字 → 視為 PASS score=1）
- pass_threshold 預設 0.8（AC-001 §pass rate）

Phase 2 升級：接 Haiku LLM judge（語意比對 + 自然語句評分）。Phase 1 簡單版
也夠用——expected_keywords 是 expert 在輸入 test_case 時人工指定，等於把
語意比對成本前置到 case 撰寫階段。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DEFAULT_PASS_THRESHOLD = 0.8


@dataclass(frozen=True)
class JudgeResult:
    status: Literal["passed", "failed"]
    score: float
    reason: str


def judge_keywords(
    *,
    actual_output: str,
    expected_keywords: list[str],
    pass_threshold: float = DEFAULT_PASS_THRESHOLD,
) -> JudgeResult:
    """關鍵字白名單判斷.

    Args:
        actual_output: AI 實際回應
        expected_keywords: case 中的關鍵字 list（不分大小寫）
        pass_threshold: score 達多少視為 passed

    Returns:
        JudgeResult — status + 0~1 score + 解釋字串
    """
    if not expected_keywords:
        return JudgeResult(
            status="passed",
            score=1.0,
            reason="no expected_keywords; auto-pass",
        )

    lower = actual_output.lower()
    matched: list[str] = []
    missing: list[str] = []
    for kw in expected_keywords:
        norm = kw.strip().lower()
        if not norm:
            continue
        if norm in lower:
            matched.append(kw)
        else:
            missing.append(kw)

    total = len(matched) + len(missing)
    if total == 0:
        return JudgeResult(
            status="passed",
            score=1.0,
            reason="no usable keywords; auto-pass",
        )

    score = len(matched) / total
    status: Literal["passed", "failed"] = "passed" if score >= pass_threshold else "failed"
    reason = f"matched={len(matched)}/{total}; missing={missing[:5]}"
    return JudgeResult(status=status, score=score, reason=reason)
