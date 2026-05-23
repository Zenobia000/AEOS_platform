"""LLMJudge unit tests — JSON parse + fallback + Judge protocol compliance."""

from __future__ import annotations

from typing import Any

import pytest

from app.llm.client import LLMClient, LLMResponse, LLMUsage
from app.services.test_judge import (
    KeywordJudge,
    LLMJudge,
    _parse_llm_score,
)


class _StubLLM(LLMClient):
    def __init__(self, text: str, *, raise_exc: Exception | None = None) -> None:
        self._text = text
        self._raise = raise_exc
        self.calls: list[dict[str, Any]] = []

    async def complete(self, **kwargs: Any) -> LLMResponse:
        self.calls.append(kwargs)
        if self._raise is not None:
            raise self._raise
        return LLMResponse(
            text=self._text,
            tool_uses=[],
            stop_reason="end_turn",
            usage=LLMUsage(input_tokens=20, output_tokens=10),
            model="stub-haiku",
        )


# ── _parse_llm_score ───────────────────


def test_parse_score_plain_json() -> None:
    score, reason = _parse_llm_score('{"score": 0.9, "reason": "ok"}')
    assert score == 0.9
    assert reason == "ok"


def test_parse_score_with_markdown_wrapping() -> None:
    raw = '```json\n{"score": 0.5, "reason": "部分對"}\n```'
    score, reason = _parse_llm_score(raw)
    assert score == 0.5
    assert reason == "部分對"


def test_parse_score_clamps_above_1() -> None:
    score, _ = _parse_llm_score('{"score": 2.5, "reason": "x"}')
    assert score == 1.0


def test_parse_score_clamps_below_0() -> None:
    score, _ = _parse_llm_score('{"score": -0.3, "reason": "x"}')
    assert score == 0.0


def test_parse_score_invalid_json_raises() -> None:
    with pytest.raises(ValueError, match="非合法 JSON"):
        _parse_llm_score("definitely not json")


def test_parse_score_missing_field_raises() -> None:
    with pytest.raises(ValueError, match="缺 score"):
        _parse_llm_score('{"reason": "no score field"}')


# ── LLMJudge.evaluate ──────────────────


async def test_llm_judge_passed() -> None:
    judge = LLMJudge(
        llm=_StubLLM('{"score": 0.92, "reason": "完整且正確"}'),
        pass_threshold=0.8,
    )
    result = await judge.evaluate(
        user_input="退貨多久",
        expected_outcome="7 天",
        expected_keywords=["7 天"],
        actual_output="可以在 7 天內辦理退貨",
    )
    assert result.status == "passed"
    assert result.score == 0.92
    assert "完整" in result.reason


async def test_llm_judge_failed_below_threshold() -> None:
    judge = LLMJudge(
        llm=_StubLLM('{"score": 0.5, "reason": "缺發票資訊"}'),
        pass_threshold=0.8,
    )
    result = await judge.evaluate(
        user_input="退貨多久",
        expected_outcome="7 天 + 發票",
        expected_keywords=["7 天", "發票"],
        actual_output="退貨 7 天",
    )
    assert result.status == "failed"
    assert result.score == 0.5


async def test_llm_judge_uses_haiku_model_by_default() -> None:
    stub = _StubLLM('{"score": 1.0, "reason": "ok"}')
    judge = LLMJudge(llm=stub)
    await judge.evaluate(
        user_input="a",
        expected_outcome="b",
        expected_keywords=[],
        actual_output="b",
    )
    assert stub.calls[0]["model"].startswith("claude-haiku")


async def test_llm_judge_fallback_to_keyword_on_llm_error() -> None:
    stub = _StubLLM("", raise_exc=RuntimeError("upstream LLM 500"))
    judge = LLMJudge(llm=stub, keyword_fallback_on_error=True)
    result = await judge.evaluate(
        user_input="退貨",
        expected_outcome="7 天",
        expected_keywords=["7 天"],
        actual_output="7 天內可退",
    )
    assert result.status == "passed"
    assert "fallback" in result.reason


async def test_llm_judge_no_fallback_propagates_error() -> None:
    stub = _StubLLM("", raise_exc=RuntimeError("LLM down"))
    judge = LLMJudge(llm=stub, keyword_fallback_on_error=False)
    with pytest.raises(ValueError, match="LLM judge error"):
        await judge.evaluate(
            user_input="x",
            expected_outcome="y",
            expected_keywords=[],
            actual_output="z",
        )


async def test_llm_judge_invalid_response_falls_back() -> None:
    """LLM 回了 garbage 也走 fallback（如果 enabled）."""
    judge = LLMJudge(
        llm=_StubLLM("not valid json at all"),
        keyword_fallback_on_error=True,
    )
    result = await judge.evaluate(
        user_input="x",
        expected_outcome="y",
        expected_keywords=["y"],
        actual_output="y indeed",
    )
    assert result.status == "passed"
    assert "fallback" in result.reason


# ── Judge protocol — KeywordJudge wrapping ─


async def test_keyword_judge_class_matches_function() -> None:
    judge = KeywordJudge(pass_threshold=0.5)
    result = await judge.evaluate(
        user_input="x",
        expected_outcome="y",
        expected_keywords=["foo", "bar"],
        actual_output="foo only",
    )
    assert result.status == "passed"
    assert result.score == 0.5
