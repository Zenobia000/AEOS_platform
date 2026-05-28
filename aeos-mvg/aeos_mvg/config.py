"""Environment + Anthropic client wiring for the W1 slice."""

from __future__ import annotations

import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

# Models (foundation/02 §4): opus for drafts, haiku as the eval judge.
DRAFT_MODEL = "claude-opus-4-7"
JUDGE_MODEL = "claude-haiku-4-5"


def get_client() -> anthropic.Anthropic:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit(
            "ANTHROPIC_API_KEY 未設定 — 複製 .env.example 為 .env 並填入金鑰"
        )
    return anthropic.Anthropic(api_key=key)
