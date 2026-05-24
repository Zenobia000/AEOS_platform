"""Prometheus metric definitions + FastAPI instrumentator wiring.

對應 OBS-001 §2 Golden Signals + §3 業務 KPI。

Golden Signals（HTTP 層）由 `prometheus-fastapi-instrumentator` 自動暴露：
- http_requests_total / http_request_duration_seconds histogram
- per (handler, method, status) label

業務 metric 在本檔以 module-level 物件登記（單一 default registry），
由 service / worker 程式碼直接 import 用：

    from app.observability import llm_tokens_total
    llm_tokens_total.labels(tenant_id=..., model=..., type="prompt").inc(123)

設計選擇：
- 不接 multiprocess registry（Phase 1 單 worker；多進程在 Phase 2 接 gunicorn 時補）
- tenant_id label 直接放 UUID 字串；高 cardinality 風險低（< 100 tenants pilot）
- cost 用 float counter；Phase 1 caller 算好 USD 後 .inc(amount)
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

# ── 業務 metric（OBS-001 §3） ────────────────────


llm_tokens_total = Counter(
    "aeos_llm_tokens_total",
    "LLM token usage by tenant / model / type (prompt vs completion)",
    labelnames=("tenant_id", "model", "type"),
)

llm_cost_usd_total = Counter(
    "aeos_llm_cost_usd_total",
    "LLM cost in USD by tenant / model",
    labelnames=("tenant_id", "model"),
)

e2e_latency_seconds = Histogram(
    "aeos_e2e_latency_seconds",
    "End-to-end latency per pipeline step",
    labelnames=("step",),  # webhook / llm / reply / push
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 8, 13, 21),  # NFR-001: 8s p95 target
)

conversations_total = Counter(
    "aeos_conversations_total",
    "Conversation lifecycle events",
    labelnames=("tenant_id", "status"),  # auto_resolved / escalated / abandoned
)

kb_ingest_jobs_total = Counter(
    "aeos_kb_ingest_jobs_total",
    "KB ingest job outcomes",
    labelnames=("tenant_id", "status"),  # completed / failed
)

outbound_sent_total = Counter(
    "aeos_outbound_sent_total",
    "Outbound messages successfully pushed",
    labelnames=("channel",),
)

outbound_failed_total = Counter(
    "aeos_outbound_failed_total",
    "Outbound messages permanently failed (after retries)",
    labelnames=("channel",),
)

pii_redactions_total = Counter(
    "aeos_pii_redactions_total",
    "PII redactions at webhook ingress, by kind (email/tw_mobile/etc)",
    labelnames=("tenant_id", "kind"),
)

aeos_build_info = Gauge(
    "aeos_build_info",
    "AEOS build info — value 1 with labels",
    labelnames=("version", "env"),
)


def register_app_info(*, version: str, env: str) -> None:
    """app 啟動時呼叫，把 build_info 設成 1。"""
    aeos_build_info.labels(version=version, env=env).set(1)


# ── FastAPI middleware wiring ─────────────────────


def instrument_app(app: object) -> Instrumentator:
    """掛 FastAPI middleware + 暴露 /metrics。

    內部 helper 路徑（/health / /metrics 本身）排除以避免 self-monitoring 雜訊。
    """
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        excluded_handlers=["/health", "/metrics"],
        env_var_name="AEOS_ENABLE_METRICS",
    )
    instrumentator.instrument(app)  # type: ignore[arg-type]
    return instrumentator
