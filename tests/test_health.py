"""Smoke tests for meta endpoints."""

from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "env" in body
    assert "version" in body


async def test_metrics_returns_placeholder(client: AsyncClient) -> None:
    response = await client.get("/metrics")

    assert response.status_code == 200
    assert "aeos_build_info" in response.text


async def test_metrics_prometheus_format(client: AsyncClient) -> None:
    """確認 /metrics 回 Prometheus exposition 格式（# HELP + # TYPE markers）。"""
    response = await client.get("/metrics")
    assert response.status_code == 200
    text_body = response.text
    assert "# HELP" in text_body
    assert "# TYPE" in text_body
    # content-type 應是 prometheus
    assert response.headers["content-type"].startswith("text/plain")


# Phase 1 後續 #2: /health/ready DB ping ───────────


async def test_health_ready_with_db(client: AsyncClient) -> None:
    """/health/ready 跑 DB SELECT 1；成功回 200 + checks.db='ok'。"""
    response = await client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["app"] == "ok"
    assert body["checks"]["db"] == "ok"
