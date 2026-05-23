"""Notifications service — Slack webhook 通知 (S5).

Phase 1：純 outgoing webhook，不接收互動。
- kill_switch.disable_ai → P0 通知
- kill_switch.enable_ai → P0 通知（恢復）
- outbound permanent fail → P1 通知
- 後續可加 P0 alert: AeosApiDown / DLQ growing 等

SLACK_WEBHOOK_URL 未設時 silently skip — dev / test 不需要真實 webhook。
失敗（網路 / Slack 5xx）只 log warning，不阻擋業務流（這是 best-effort
通知，不是業務 invariant）。
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger("aeos.notifications")

SEVERITY_EMOJI = {
    "P0": "🚨",
    "P1": "⚠️",
    "P2": "ℹ️",
    "info": "✅",
}


async def notify_slack(
    *,
    severity: str,
    title: str,
    message: str,
    fields: dict[str, Any] | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> bool:
    """送 Slack incoming webhook。

    Args:
        severity: 'P0' / 'P1' / 'P2' / 'info'
        title: 短標題（appear in notification preview）
        message: 主要說明
        fields: 結構化資料（key/value pairs）顯示為 Slack attachment fields
        http_client: 注入用（測試）；None 則建立暫時 client

    Returns:
        True if sent (200); False if skipped or failed (best-effort).
    """
    settings = get_settings()
    webhook = settings.slack_webhook_url
    if not webhook:
        logger.debug("SLACK_WEBHOOK_URL not set; skipping notify '%s'", title)
        return False

    emoji = SEVERITY_EMOJI.get(severity, "ℹ️")
    text = f"{emoji} [{severity}] *{title}*\n{message}"
    payload: dict[str, Any] = {"text": text}
    if fields:
        payload["attachments"] = [
            {
                "color": _severity_color(severity),
                "fields": [
                    {"title": k, "value": str(v), "short": len(str(v)) < 40}
                    for k, v in fields.items()
                ],
            }
        ]

    owned_client = http_client is None
    client = http_client or httpx.AsyncClient(timeout=5.0)
    try:
        resp = await client.post(webhook, json=payload, timeout=5.0)
        if resp.status_code == 200:
            return True
        logger.warning("Slack webhook returned %d: %s", resp.status_code, resp.text[:200])
        return False
    except Exception as exc:  # network / timeout
        logger.warning("Slack notify failed: %s", exc)
        return False
    finally:
        if owned_client:
            await client.aclose()


def _severity_color(severity: str) -> str:
    return {
        "P0": "danger",
        "P1": "warning",
        "P2": "#888888",
        "info": "good",
    }.get(severity, "#888888")
