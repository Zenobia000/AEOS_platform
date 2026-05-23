"""Slack notifications service tests — skip / send / failure best-effort."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import httpx
import pytest

from app.config import Settings, get_settings
from app.services import notifications


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Generator[None, None, None]:
    """每個測試前清掉 lru_cache 的 settings；測完還原."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def test_notify_skip_when_no_webhook(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("slack_webhook_url", raising=False)
    # 也清掉 .env 那一層
    monkeypatch.setattr(notifications, "get_settings", lambda: Settings(slack_webhook_url=None))
    sent = await notifications.notify_slack(severity="P0", title="X", message="should not send")
    assert sent is False


async def test_notify_sends_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["payload"] = request.content.decode()
        return httpx.Response(200, text="ok")

    transport = httpx.MockTransport(_handler)
    monkeypatch.setattr(
        notifications,
        "get_settings",
        lambda: Settings(slack_webhook_url="https://hooks.slack.com/services/T/B/C"),
    )

    async with httpx.AsyncClient(transport=transport) as client:
        sent = await notifications.notify_slack(
            severity="P0",
            title="Kill switch",
            message="AI disabled",
            fields={"tenant_id": "t-1", "reason": "incident"},
            http_client=client,
        )

    assert sent is True
    assert captured["url"] == "https://hooks.slack.com/services/T/B/C"
    assert "Kill switch" in captured["payload"]
    assert "AI disabled" in captured["payload"]
    assert "tenant_id" in captured["payload"]


async def test_notify_returns_false_on_500(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = httpx.MockTransport(lambda _r: httpx.Response(500, text="boom"))
    monkeypatch.setattr(
        notifications,
        "get_settings",
        lambda: Settings(slack_webhook_url="https://hooks.slack.com/services/X"),
    )
    async with httpx.AsyncClient(transport=transport) as client:
        sent = await notifications.notify_slack(
            severity="P1",
            title="x",
            message="y",
            http_client=client,
        )
    assert sent is False  # best-effort：500 不 raise


async def test_notify_returns_false_on_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _handler(_r: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("dns fail")

    transport = httpx.MockTransport(_handler)
    monkeypatch.setattr(
        notifications,
        "get_settings",
        lambda: Settings(slack_webhook_url="https://hooks.slack.com/services/X"),
    )
    async with httpx.AsyncClient(transport=transport) as client:
        sent = await notifications.notify_slack(
            severity="P0",
            title="x",
            message="y",
            http_client=client,
        )
    assert sent is False  # best-effort：不 raise


async def test_severity_emoji_in_text(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    def _handler(r: httpx.Request) -> httpx.Response:
        captured["body"] = r.content.decode()
        return httpx.Response(200)

    transport = httpx.MockTransport(_handler)
    monkeypatch.setattr(
        notifications,
        "get_settings",
        lambda: Settings(slack_webhook_url="https://hooks.slack.com/services/X"),
    )
    async with httpx.AsyncClient(transport=transport) as client:
        await notifications.notify_slack(
            severity="P0",
            title="t",
            message="m",
            http_client=client,
        )
    assert "🚨" in captured["body"]
    assert "[P0]" in captured["body"]
