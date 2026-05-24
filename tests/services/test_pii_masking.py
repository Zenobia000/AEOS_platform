"""PII masking unit tests."""

from __future__ import annotations

from app.services.pii_masking import _luhn_valid, mask_text

# ── basic patterns ──


def test_email_masked() -> None:
    r = mask_text("contact me at john.doe@example.com please")
    assert "[REDACTED:email]" in r.masked
    assert "john.doe" not in r.masked
    assert r.redactions == {"email": 1}


def test_tw_mobile_masked() -> None:
    for phone in ["0912345678", "0912-345-678", "0912 345 678"]:
        r = mask_text(f"打給我 {phone} 謝謝")
        assert "[REDACTED:tw_mobile]" in r.masked
        assert phone not in r.masked


def test_tw_landline_masked() -> None:
    for phone in ["02-2345-6789", "(02)2345-6789", "07-1234-5678"]:
        r = mask_text(f"市話 {phone}")
        assert "[REDACTED:tw_landline]" in r.masked


def test_tw_id_masked() -> None:
    r = mask_text("身分證 A123456789")
    assert "[REDACTED:tw_id]" in r.masked
    assert "A123456789" not in r.masked


def test_invalid_tw_id_not_masked() -> None:
    """A123456789 開頭必是 [12] 才算合法 ID；A3xxx 不應 mask."""
    r = mask_text("A323456789 not id")
    assert "[REDACTED:tw_id]" not in r.masked


def test_credit_card_with_luhn_masked() -> None:
    # 4111-1111-1111-1111 是 Luhn 合法的 Visa 測試卡號
    r = mask_text("我的卡 4111-1111-1111-1111 過期")
    assert "[REDACTED:credit_card]" in r.masked


def test_credit_card_invalid_luhn_not_masked_as_card() -> None:
    """13-19 位但 Luhn 失敗的數字串可能被當 bank_like，不該誤判 credit_card."""
    # 1234567890123 (13 digits, Luhn fail)
    r = mask_text("純亂數 1234567890123")
    assert "[REDACTED:credit_card]" not in r.masked


def test_bank_like_long_digits_masked() -> None:
    r = mask_text("帳號 12345678901")  # 11 位
    assert "[REDACTED:bank_like]" in r.masked


# ── multi-PII ──


def test_multiple_pii_in_one_text() -> None:
    text = "我的 email 是 user@foo.com，手機 0912-345-678，身分證 B187654321，謝謝"
    r = mask_text(text)
    assert r.total_redactions == 3
    assert r.redactions == {"email": 1, "tw_mobile": 1, "tw_id": 1}
    assert "user@foo.com" not in r.masked
    assert "0912-345-678" not in r.masked
    assert "B187654321" not in r.masked


def test_no_pii_returns_unchanged() -> None:
    r = mask_text("你好，請問退貨怎麼辦？")
    assert r.masked == "你好，請問退貨怎麼辦？"
    assert r.total_redactions == 0


def test_empty_input() -> None:
    r = mask_text("")
    assert r.masked == ""
    assert r.total_redactions == 0


# ── Luhn ──


def test_luhn_valid_visa() -> None:
    assert _luhn_valid("4111111111111111") is True


def test_luhn_invalid() -> None:
    assert _luhn_valid("4111111111111112") is False
    assert _luhn_valid("123") is False  # too short
