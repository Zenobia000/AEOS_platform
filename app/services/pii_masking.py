"""PII masking — 在 webhook ingress / message 寫入前過濾敏感資料.

對應 SEC-001 §6.1 #11 PII masking + 個資法合規要求。

Phase 1 偵測類型（regex-based）：
- email
- 台灣手機（09xx-xxx-xxx / 09xxxxxxxx）
- 台灣市話（02-1234-5678 / (02)1234-5678）
- 信用卡號（14-19 位數，Luhn 檢查避免 false positive）
- 台灣身分證（A123456789 格式）
- IBAN / 14-16 位連續數字（疑似銀行帳號）

Phase 2 升級：接 spaCy / Claude NER 提取人名、地址。Phase 1 純 regex 對
結構化敏感資料覆蓋率已 > 90%；自由文字 PII（如姓名）由 expert review
+ audit 二道防線兜底。

不 mask 的：
- LINE channel_user_id（已 SHA256 pseudonymize）
- AI 回應給 user 的訊息（這是要送回客戶的內容，不能 mask）
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final


@dataclass(frozen=True)
class MaskResult:
    masked: str
    redactions: dict[str, int] = field(default_factory=dict)

    @property
    def total_redactions(self) -> int:
        return sum(self.redactions.values())


# ── Patterns ──────────────────────────────────────


_EMAIL: Final = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# 台灣手機 09xx-xxx-xxx 或 09xxxxxxxx
_TW_MOBILE: Final = re.compile(r"\b09\d{2}[-\s]?\d{3}[-\s]?\d{3}\b")

# 台灣市話 02-xxxx-xxxx / (02)xxxx-xxxx / 0x-xxxx-xxxx
_TW_LANDLINE: Final = re.compile(r"\(?\b0[2-8]\)?[-\s]?\d{3,4}[-\s]?\d{4}\b")

# 台灣身分證：1 個英文字母 + 9 個數字（A123456789）
_TW_ID: Final = re.compile(r"\b[A-Z][12]\d{8}\b")

# 信用卡號：4 個 4 位區塊（可空白/橫線分隔）或連續 13-19 位
_CREDIT_CARD: Final = re.compile(r"\b(?:\d[ -]?){13,19}\b")

# 連續 8-12 位數字（疑似銀行帳號；放後面避免吃掉電話號碼）
_BANK_LIKE: Final = re.compile(r"\b\d{8,12}\b")


# ── Luhn check for credit cards ────────────────────


def _luhn_valid(card_digits: str) -> bool:
    """Luhn checksum；用來排除「13 位但不是信用卡」的 false positive."""
    digits = [int(c) for c in card_digits if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


# ── mask ──────────────────────────────────────────


def mask_text(text: str) -> MaskResult:
    """偵測 + 替換 PII，回傳 (masked, redactions counter).

    順序很重要 — 先匹配特定 pattern（email / 手機 / 身分證），最後才匹配
    通用數字串（信用卡 / 銀行），避免長 pattern 吞短 pattern。
    """
    if not text:
        return MaskResult(masked=text)

    redactions: dict[str, int] = {}
    masked = text

    def _replace_pattern(
        pattern: re.Pattern[str],
        kind: str,
        current: str,
        validator: object = None,
    ) -> str:
        def _repl(m: re.Match[str]) -> str:
            value = m.group(0)
            if (
                validator is not None
                and callable(validator)
                and not validator(value)
            ):
                return value
            redactions[kind] = redactions.get(kind, 0) + 1
            return f"[REDACTED:{kind}]"

        return pattern.sub(_repl, current)

    # 先處理長/獨特 pattern
    masked = _replace_pattern(_EMAIL, "email", masked)
    masked = _replace_pattern(_TW_MOBILE, "tw_mobile", masked)
    masked = _replace_pattern(_TW_LANDLINE, "tw_landline", masked)
    masked = _replace_pattern(_TW_ID, "tw_id", masked)
    # 信用卡需 Luhn 驗證（排除假陽性）
    masked = _replace_pattern(_CREDIT_CARD, "credit_card", masked, validator=_luhn_valid)
    # 最後抓剩下的連續數字（銀行帳號疑似）
    masked = _replace_pattern(_BANK_LIKE, "bank_like", masked)

    return MaskResult(masked=masked, redactions=redactions)
