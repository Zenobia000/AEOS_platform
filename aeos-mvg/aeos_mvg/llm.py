"""Anthropic SDK wrapper: draft generation (opus) + LLM-as-judge (haiku).

Prompt caching is the cost lever (foundation/03 B4, ≤ $300/month). The knowledge
base is a stable system-prompt prefix shared across every question in an eval run,
so we mark it `cache_control: ephemeral`. First call writes the cache (~1.25x),
the rest read it (~0.1x). Verify via usage.cache_read_input_tokens.

Caching invariant: the system blocks (instructions + knowledge) must be
byte-identical across calls, and the volatile part (the question) goes in
`messages` AFTER the cached prefix. Min cacheable prefix on opus-4-7 is ~4096
tokens — smaller knowledge bases silently won't cache (no error).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from .config import DRAFT_MODEL, JUDGE_MODEL, get_client

# --- Draft generation -------------------------------------------------------

DRAFT_SYSTEM_INSTRUCTIONS = """你是一位客服 AI 員工，依「知識庫」為客戶問題草擬可直接送出的回覆。

鐵律：
1. 只根據知識庫內容回答。禁止編造知識庫沒有的事實、數字、政策、承諾。
2. 若知識庫不足以回答，整則回覆必須以 `[需人工]` 開頭，後接一句說明缺什麼依據，絕不硬掰。
3. 語氣專業、簡潔、友善。直接給可送出的回覆本文，不要加「以下是草稿」之類前綴。
"""

NEEDS_HUMAN_MARKER = "[需人工]"


@dataclass(slots=True)
class DraftResult:
    text: str
    needs_human: bool
    usage: object  # anthropic Usage; read cache_read_input_tokens etc.


def generate_draft(question: str, knowledge: str) -> DraftResult:
    client = get_client()
    system = [
        {"type": "text", "text": DRAFT_SYSTEM_INSTRUCTIONS},
        {
            "type": "text",
            "text": f"# 知識庫\n\n{knowledge}",
            "cache_control": {"type": "ephemeral"},
        },
    ]
    resp = client.messages.create(
        model=DRAFT_MODEL,
        max_tokens=1024,
        thinking={"type": "disabled"},  # grounded CS reply: direct, cost-controlled
        system=system,
        messages=[{"role": "user", "content": question}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    return DraftResult(
        text=text,
        needs_human=text.startswith(NEEDS_HUMAN_MARKER),
        usage=resp.usage,
    )


# --- LLM-as-judge -----------------------------------------------------------

JUDGE_SYSTEM = """你是嚴格的客服品質評審，模擬資深客服主管審核 AI 草稿。

依「客戶問題 + 參考答案 + AI 草稿」判定主管會怎麼處理這份草稿：
- approve：可原樣送出（事實正確、切題、語氣得體）。這是最強訊號。
- edit：方向對但需小修才可送（漏細節、語氣或措辭要調）。
- reject：不可送（事實錯誤、答非所問、幻覺、或該轉人工卻硬答）。

判準：以參考答案為事實基準。草稿捏造參考答案沒有的內容一律 reject。
草稿以 `[需人工]` 開頭時：若參考答案其實有解 → reject（代表知識缺漏）；
若參考答案本身也說明須轉人工 → approve。
"""


class JudgeVerdict(BaseModel):
    verdict: Literal["approve", "edit", "reject"]
    reason: str


def judge_draft(question: str, draft: str, reference: str) -> JudgeVerdict:
    client = get_client()
    user = (
        f"客戶問題：\n{question}\n\n"
        f"參考答案（事實基準）：\n{reference}\n\n"
        f"AI 草稿：\n{draft}"
    )
    resp = client.messages.parse(
        model=JUDGE_MODEL,
        max_tokens=512,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": user}],
        output_format=JudgeVerdict,
    )
    if resp.parsed_output is None:  # safety refusal or schema miss
        return JudgeVerdict(verdict="reject", reason="judge 無法產生結構化判定")
    return resp.parsed_output
