"""search_knowledge — RAG retrieval over KnowledgeCard.

依 MC-008 §檢索 + skills/customer-service/faq-respond/v1.0.0/tools.yaml:
- input: { query: str, top_k?: int, min_score?: float }
- output: list of { kc_id, title, excerpt, score }
- 用 pgvector 餘弦距離 `<=>` ORDER BY embedding
- 只搜 status='approved' 的 KC（drafts/archived 不出現給 LLM）

Phase 1 簡化：
- 由 caller 提供 query_embedding（在 input 內傳）；本 handler 不做 embedding 呼叫
  （embedding 服務（voyage-3-lite）會在更上層處理 + cache）
- 若 input 沒帶 query_embedding，回空陣列（fallback；S2 KB worker 接上後改為硬錯）
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from app.agent.tool_executor import ToolExecutionContext

DEFAULT_TOP_K = 5
DEFAULT_MIN_SCORE = 0.7


async def search_knowledge(
    tool_input: dict[str, Any],
    ctx: ToolExecutionContext,
) -> list[dict[str, Any]]:
    top_k = int(tool_input.get("top_k", DEFAULT_TOP_K))
    min_score = float(tool_input.get("min_score", DEFAULT_MIN_SCORE))
    query_embedding = tool_input.get("query_embedding")

    if query_embedding is None:
        return []  # Phase 1 fallback；S2 KB worker 接上後改 raise

    # pgvector cosine distance: <=> ；score = 1 - distance
    qv = "[" + ",".join(str(float(v)) for v in query_embedding) + "]"
    rows = (
        await ctx.session.execute(
            text(
                "SELECT id, title, "
                "LEFT(body_markdown, 500) AS excerpt, "
                "1 - (embedding <=> CAST(:qv AS vector)) AS score "
                "FROM knowledge_card "
                "WHERE tenant_id = :tid "
                "  AND status = 'approved' "
                "  AND embedding IS NOT NULL "
                "ORDER BY embedding <=> CAST(:qv AS vector) "
                "LIMIT :lim"
            ),
            {"tid": str(ctx.tenant_id), "qv": qv, "lim": top_k},
        )
    ).all()

    results: list[dict[str, Any]] = []
    for kc_id, title, excerpt, score in rows:
        if score is None or float(score) < min_score:
            continue
        results.append(
            {
                "kc_id": str(kc_id),
                "title": title,
                "excerpt": excerpt,
                "score": round(float(score), 4),
            }
        )
    return results
