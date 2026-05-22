"""/metrics endpoint exposes prometheus_client default registry."""

from __future__ import annotations

from httpx import AsyncClient


async def test_metrics_endpoint_returns_prometheus_text(client: AsyncClient) -> None:
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert "aeos_build_info" in body
    # FastAPI instrumentator 自動暴露的 HTTP metric
    assert "http_request" in body or "http_requests" in body


async def test_metrics_endpoint_content_type(client: AsyncClient) -> None:
    resp = await client.get("/metrics")
    ctype = resp.headers.get("content-type", "")
    assert "text/plain" in ctype
