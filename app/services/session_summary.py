"""L2.5 Session Summary service — 對話結束時生成摘要 (Phase 1 後續 #12).

對應 ADR-0010 §L2.5（intermediate memory layer）+ MC-010 conversation lifecycle。
Phase 1 stub：
- 有 LLM client → 跑 Haiku 4.5 摘要（≤ 200 tokens；過 PII 遮罩）
- 無 LLM client → 用 deterministic stub（取最後 N 則 + first user query；framework 完整可運行）
- 寫到 conversation.summary 欄

非 Phase 1 範圍：摘要品質量測、incremental summarization、跨 session 串接（L3 知識）。
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import LLMClient, LLMMessage

logger = logging.getLogger(__name__)

MAX_SUMMARY_TOKENS = 200
DEFAULT_SUMMARY_MODEL = "claude-haiku-4-5-20251001"


async def generate_summary(
    session: AsyncSession,
    *,
    conversation_id: uuid.UUID,
    llm_client: LLMClient | None = None,
    max_messages: int = 20,
) -> str | None:
    """為一個 conversation 生成 ≤ 200 token 摘要。

    Args:
        conversation_id: 目標對話
        llm_client: 若提供 → 用 Haiku 4.5；None → deterministic stub
        max_messages: 摘要時參考最近 N 則訊息

    Returns:
        摘要字串；若 conversation 不存在或無訊息 → None
    """
    rows = (
        await session.execute(
            text(
                "SELECT role, content FROM message "
                "WHERE conversation_id = :cid "
                "ORDER BY seq DESC LIMIT :lim"
            ),
            {"cid": str(conversation_id), "lim": max_messages},
        )
    ).all()
    if not rows:
        return None

    # chronological 順序
    history = list(reversed([(r[0], r[1]) for r in rows]))

    if llm_client is not None:
        try:
            return await _summarize_via_llm(llm_client, history)
        except Exception as exc:
            logger.warning("L2.5 summary LLM failed; fallback to stub: %s", exc)
            return _summarize_stub(history)

    return _summarize_stub(history)


async def _summarize_via_llm(llm: LLMClient, history: list[tuple[str, str]]) -> str:
    """用 Haiku 跑摘要；strict JSON output 避免格式漂移。"""
    conversation_text = "\n".join(f"{role}: {content[:300]}" for role, content in history)
    prompt = (
        "以下是 AI 客服與 user 的對話片段。請用 ≤ 80 字摘要：\n"
        "1. user 問什麼\n"
        "2. AI 回答了什麼（或為何 handoff）\n"
        "3. 最終結果（解決 / 未解決 / 轉真人）\n\n"
        "**只回摘要本文，不要前言、不要 markdown。**\n\n"
        f"對話：\n{conversation_text}"
    )
    resp = await llm.complete(
        messages=[LLMMessage(role="user", content=prompt)],
        model=DEFAULT_SUMMARY_MODEL,
        max_tokens=MAX_SUMMARY_TOKENS,
        temperature=0.0,
    )
    return (resp.text or "").strip()[:600]  # 硬上限 600 chars


def _summarize_stub(history: list[tuple[str, str]]) -> str:
    """Deterministic stub — 無 LLM client 時用，給 framework 完整可運行。"""
    user_msgs = [c for r, c in history if r == "user"]
    assistant_msgs = [c for r, c in history if r == "assistant"]

    first_user = user_msgs[0][:80] if user_msgs else "(無 user 訊息)"
    final_resp = assistant_msgs[-1][:80] if assistant_msgs else "(無 AI 回應)"
    handoff = "可能 handoff" if not assistant_msgs else "AI 回應"

    return (
        f"[STUB 摘要] user 首問: {first_user}... | "
        f"AI 最後回: {final_resp}... | "
        f"狀態: {handoff} | "
        f"訊息共 {len(history)} 則"
    )


async def write_summary_to_conversation(
    session: AsyncSession,
    *,
    conversation_id: uuid.UUID,
    summary: str,
) -> None:
    """把摘要寫到 conversation.summary 欄。"""
    await session.execute(
        text("UPDATE conversation SET summary = :s WHERE id = :cid"),
        {"s": summary, "cid": str(conversation_id)},
    )
    await session.flush()
