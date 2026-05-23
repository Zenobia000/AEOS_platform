"""業務 metric 物件 sanity test — counter inc + label cardinality."""

from __future__ import annotations

from prometheus_client import generate_latest

from app.observability import (
    conversations_total,
    kb_ingest_jobs_total,
    llm_cost_usd_total,
    llm_tokens_total,
    outbound_failed_total,
    outbound_sent_total,
    register_app_info,
)


def _dump() -> str:
    return generate_latest().decode()


def test_llm_tokens_inc_emits_metric() -> None:
    llm_tokens_total.labels(tenant_id="t-test", model="claude-sonnet", type="prompt").inc(42)
    body = _dump()
    assert 'aeos_llm_tokens_total{model="claude-sonnet"' in body
    assert 'tenant_id="t-test"' in body


def test_llm_cost_counter() -> None:
    llm_cost_usd_total.labels(tenant_id="t-cost", model="claude-haiku").inc(0.0125)
    body = _dump()
    assert "aeos_llm_cost_usd_total" in body


def test_kb_ingest_jobs_counter() -> None:
    kb_ingest_jobs_total.labels(tenant_id="t-kb", status="completed").inc()
    kb_ingest_jobs_total.labels(tenant_id="t-kb", status="failed").inc()
    body = _dump()
    assert 'aeos_kb_ingest_jobs_total{status="completed"' in body
    assert 'aeos_kb_ingest_jobs_total{status="failed"' in body


def test_outbound_counters() -> None:
    outbound_sent_total.labels(channel="line").inc()
    outbound_failed_total.labels(channel="line").inc(2)
    body = _dump()
    assert "aeos_outbound_sent_total" in body
    assert "aeos_outbound_failed_total" in body


def test_conversations_total_counter() -> None:
    conversations_total.labels(tenant_id="t-cv", status="auto_resolved").inc()
    body = _dump()
    assert 'aeos_conversations_total{status="auto_resolved"' in body


def test_register_app_info_sets_gauge_to_1() -> None:
    register_app_info(version="0.0.1-test", env="test")
    body = _dump()
    assert 'aeos_build_info{env="test",version="0.0.1-test"} 1.0' in body
