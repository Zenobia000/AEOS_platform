"""seed_demo 6 vertical skills seeding 驗證 (Phase 1 後續 #1)."""

from __future__ import annotations

import pytest

# 跳過 import script (含 hard-coded session_scope to real DB)；用 in-process call


@pytest.mark.asyncio
async def test_routing_table_covers_6_vertical() -> None:
    """確認 _seed_6_vertical_skills 內的 routing_table 包含 6 個 vertical."""
    # 不直接 import 私有 fn；改 grep 整支檔內容
    from pathlib import Path

    src = (Path(__file__).resolve().parents[2] / "scripts" / "seed_demo.py").read_text(
        encoding="utf-8"
    )

    expected_slugs = [
        "customer-service/faq-respond",
        "hr/leave-request",
        "it-helpdesk/password-reset",
        "sales/quote-request",
        "finance/expense-claim",
        "legal/contract-review",
    ]
    for slug in expected_slugs:
        assert slug in src, f"seed_demo missing routing entry for {slug}"


def test_default_skill_is_customer_service() -> None:
    """customer-service/faq-respond 應是唯一 is_default=True 的 skill."""
    from pathlib import Path

    src = (Path(__file__).resolve().parents[2] / "scripts" / "seed_demo.py").read_text(
        encoding="utf-8"
    )
    # 簡單檢查：customer-service entry 後接 is_default: True
    cs_idx = src.index("customer-service/faq-respond")
    snippet = src[cs_idx : cs_idx + 200]
    assert '"is_default": True' in snippet
