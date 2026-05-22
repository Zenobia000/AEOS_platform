"""Test judge unit tests — keyword matching score."""

from __future__ import annotations

from app.services.test_judge import judge_keywords


def test_all_keywords_present_passes() -> None:
    r = judge_keywords(
        actual_output="您好，本店退貨可於 7 天內申請，請保留發票",
        expected_keywords=["退貨", "7 天", "發票"],
    )
    assert r.status == "passed"
    assert r.score == 1.0


def test_partial_above_threshold_passes() -> None:
    r = judge_keywords(
        actual_output="本店退貨可於 7 天內辦理",
        expected_keywords=["退貨", "7 天", "發票", "保留"],
        pass_threshold=0.5,
    )
    assert r.status == "passed"
    assert 0.49 < r.score <= 0.51


def test_partial_below_threshold_fails() -> None:
    r = judge_keywords(
        actual_output="一切以官方公告為準",
        expected_keywords=["退貨", "發票", "7 天"],
    )
    assert r.status == "failed"
    assert r.score == 0.0


def test_no_keywords_auto_passes() -> None:
    r = judge_keywords(
        actual_output="您好",
        expected_keywords=[],
    )
    assert r.status == "passed"
    assert r.score == 1.0
    assert "no expected_keywords" in r.reason


def test_case_insensitive() -> None:
    r = judge_keywords(
        actual_output="Hello World",
        expected_keywords=["HELLO", "world"],
    )
    assert r.status == "passed"
    assert r.score == 1.0


def test_empty_keywords_in_list_filtered() -> None:
    r = judge_keywords(
        actual_output="hello",
        expected_keywords=["hello", "  ", ""],
    )
    assert r.status == "passed"
    assert r.score == 1.0


def test_reason_includes_missing() -> None:
    r = judge_keywords(
        actual_output="退貨可在 14 天",
        expected_keywords=["退貨", "7 天", "發票"],
    )
    assert r.status == "failed"
    assert "missing" in r.reason
    assert "7 天" in r.reason or "發票" in r.reason
