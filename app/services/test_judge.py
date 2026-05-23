"""Test judge — 判斷 AI 輸出是否符合預期 (S3 / AC-001).

提供兩種 judge 策略：
- KeywordJudge (Phase 1)：關鍵字白名單法
- LLMJudge (S5 升級)：Haiku 語意比對 — 比 keyword 更貼近真實 pass rate

兩者實作同一個 `Judge` Protocol，TestSetRunner 透過注入決定用哪個。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal, Protocol

from app.llm.client import LLMClient, LLMMessage

DEFAULT_PASS_THRESHOLD = 0.8
DEFAULT_JUDGE_MODEL = "claude-haiku-4-5"


@dataclass(frozen=True)
class JudgeResult:
    status: Literal["passed", "failed"]
    score: float
    reason: str


class Judge(Protocol):
    """test case judge 策略介面."""

    async def evaluate(
        self,
        *,
        user_input: str,
        expected_outcome: str,
        expected_keywords: list[str],
        actual_output: str,
    ) -> JudgeResult: ...


# ── Keyword judge（Phase 1 簡單版） ───────────────


def judge_keywords(
    *,
    actual_output: str,
    expected_keywords: list[str],
    pass_threshold: float = DEFAULT_PASS_THRESHOLD,
) -> JudgeResult:
    """關鍵字白名單判斷．

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


class KeywordJudge:
    """Keyword 比對 Judge — Phase 1 簡單版。"""

    def __init__(self, *, pass_threshold: float = DEFAULT_PASS_THRESHOLD) -> None:
        self._pass_threshold = pass_threshold

    async def evaluate(
        self,
        *,
        user_input: str,
        expected_outcome: str,
        expected_keywords: list[str],
        actual_output: str,
    ) -> JudgeResult:
        return judge_keywords(
            actual_output=actual_output,
            expected_keywords=expected_keywords,
            pass_threshold=self._pass_threshold,
        )


# ── LLM judge (S5 升級；Haiku 語意比對) ───────────


_LLM_JUDGE_SYSTEM = """你是一個嚴謹的測試評審。你的任務是比對 AI 回應是否
達成 expected outcome。請只回傳 JSON，格式必須是：
{"score": <0~1 的小數>, "reason": "<簡短中文評語，不超過 80 字>"}

評分標準：
- 1.0 = 完全達成，所有重要資訊都涵蓋
- 0.8 = 大致達成，可能有小遺漏
- 0.5 = 部分達成，有錯誤或關鍵資訊缺失
- 0.0 = 完全錯誤 / 跑題 / 拒答

不要 markdown 包裝、不要其他說明文字，只輸出單一 JSON object。
"""


_JSON_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)


def _parse_llm_score(raw: str) -> tuple[float, str]:
    """容錯 parse — LLM 可能回 markdown / 多餘文字，抓出 {} 區段."""
    match = _JSON_RE.search(raw)
    candidate = match.group(0) if match else raw
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(f"judge LLM 回傳非合法 JSON: {raw[:200]}") from exc
    raw_score = data.get("score")
    if not isinstance(raw_score, int | float):
        raise ValueError(f"judge LLM 缺 score 欄位: {raw[:200]}")
    score = max(0.0, min(1.0, float(raw_score)))
    reason = str(data.get("reason", ""))[:200]
    return score, reason


class LLMJudge:
    """Haiku-based 語意 judge — 給定 expected_outcome 用 LLM 評分.

    Args:
        llm: LLMClient（real or fake）
        model: 使用模型；預設 Haiku 4.5（低成本 / 高速）
        pass_threshold: ≥ 此分數視為 passed
        keyword_fallback_on_error: LLM 失敗時自動降級為 keyword judge
    """

    def __init__(
        self,
        *,
        llm: LLMClient,
        model: str = DEFAULT_JUDGE_MODEL,
        pass_threshold: float = DEFAULT_PASS_THRESHOLD,
        keyword_fallback_on_error: bool = True,
    ) -> None:
        self._llm = llm
        self._model = model
        self._pass_threshold = pass_threshold
        self._keyword_fallback = keyword_fallback_on_error

    async def evaluate(
        self,
        *,
        user_input: str,
        expected_outcome: str,
        expected_keywords: list[str],
        actual_output: str,
    ) -> JudgeResult:
        prompt = (
            f"使用者問題：{user_input}\n\n"
            f"期望結果：{expected_outcome}\n\n"
            f"關鍵字（可選參考）：{', '.join(expected_keywords) or '無'}\n\n"
            f"AI 實際回答：{actual_output}\n\n"
            "請以前述 JSON 格式回覆。"
        )
        try:
            response = await self._llm.complete(
                messages=[LLMMessage(role="user", content=prompt)],
                system=_LLM_JUDGE_SYSTEM,
                max_tokens=200,
                temperature=0.0,
                model=self._model,
            )
            score, reason = _parse_llm_score(response.text)
        except Exception as exc:
            if self._keyword_fallback:
                fallback = judge_keywords(
                    actual_output=actual_output,
                    expected_keywords=expected_keywords,
                    pass_threshold=self._pass_threshold,
                )
                # 用 keyword fallback 結果，但 reason 標明已 fallback
                return JudgeResult(
                    status=fallback.status,
                    score=fallback.score,
                    reason=f"[llm-judge failed → keyword fallback] {fallback.reason}",
                )
            raise ValueError(f"LLM judge error: {exc}") from exc

        status: Literal["passed", "failed"] = (
            "passed" if score >= self._pass_threshold else "failed"
        )
        return JudgeResult(status=status, score=score, reason=reason)
