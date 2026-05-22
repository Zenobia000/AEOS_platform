"""KCReview service — KnowledgeCard draft review approve / edit / archive.

依 PRD-001 §5.1 F-KB-04 + MC-008:
- KB ingest worker 寫 KC (status='draft')
- Expert 1-click approve → 'approved' + approved_by + approved_at
  （進 KB；可被 search_knowledge 撈到）
- Expert edit-and-approve → 更新 title/body/tags/card_type → 'approved'
- Expert archive → 'archived'（不被檢索，但保留 audit trace）

所有動作走 audit_log（kc.draft_approved / kc.draft_edited / kc.archived），
作為 Skill 訓練 + 合規追溯素材。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.knowledge_card import KC_CARD_TYPES, KnowledgeCard
from app.services import audit


class KCReviewError(RuntimeError):
    """Expert action 無法執行（status 不對 / KC 不存在 / 欄位不合法等）."""


@dataclass(frozen=True)
class KCReviewResult:
    kc_id: uuid.UUID
    action: Literal["approved", "edited", "archived"]
    new_status: str


async def _load_draft(session: AsyncSession, kc_id: uuid.UUID) -> KnowledgeCard:
    kc = (
        await session.execute(select(KnowledgeCard).where(KnowledgeCard.id == kc_id))
    ).scalar_one_or_none()
    if kc is None:
        raise KCReviewError(f"knowledge_card {kc_id} not found")
    if kc.status != "draft":
        raise KCReviewError(f"knowledge_card {kc_id} not in draft (status={kc.status})")
    return kc


async def approve(
    session: AsyncSession,
    *,
    kc_id: uuid.UUID,
    expert_id: str,
) -> KCReviewResult:
    """Expert 1-click approve → 'approved'."""
    kc = await _load_draft(session, kc_id)
    kc.status = "approved"
    kc.approved_by = expert_id
    kc.approved_at = datetime.now(UTC)
    await session.flush()

    await audit.emit(
        session,
        event_type="kc.draft_approved",
        tenant_id=kc.tenant_id,
        actor_id=expert_id,
        resource_type="knowledge_card",
        resource_id=str(kc.id),
        payload={"card_type": kc.card_type, "title_snippet": kc.title[:80]},
    )
    return KCReviewResult(kc_id=kc.id, action="approved", new_status="approved")


async def edit_and_approve(
    session: AsyncSession,
    *,
    kc_id: uuid.UUID,
    expert_id: str,
    title: str | None = None,
    body_markdown: str | None = None,
    tags: list[str] | None = None,
    card_type: str | None = None,
) -> KCReviewResult:
    """Expert 編輯欄位後 approve。所有欄位都是 optional，但至少要動一個。"""
    if title is None and body_markdown is None and tags is None and card_type is None:
        raise KCReviewError("edit requires at least one field change")
    if title is not None and not title.strip():
        raise KCReviewError("title cannot be empty")
    if body_markdown is not None and not body_markdown.strip():
        raise KCReviewError("body_markdown cannot be empty")
    if card_type is not None and card_type not in KC_CARD_TYPES:
        raise KCReviewError(f"card_type {card_type!r} not in {KC_CARD_TYPES}")

    kc = await _load_draft(session, kc_id)
    changes: dict[str, object] = {}
    if title is not None and title != kc.title:
        kc.title = title
        changes["title"] = title[:80]
    if body_markdown is not None and body_markdown != kc.body_markdown:
        kc.body_markdown = body_markdown
        changes["body_length"] = len(body_markdown)
    if tags is not None and tags != list(kc.tags):
        kc.tags = list(tags)
        changes["tags"] = tags
    if card_type is not None and card_type != kc.card_type:
        kc.card_type = card_type
        changes["card_type"] = card_type

    kc.status = "approved"
    kc.approved_by = expert_id
    kc.approved_at = datetime.now(UTC)
    await session.flush()

    await audit.emit(
        session,
        event_type="kc.draft_edited",
        tenant_id=kc.tenant_id,
        actor_id=expert_id,
        resource_type="knowledge_card",
        resource_id=str(kc.id),
        payload={"changes": changes},
    )
    return KCReviewResult(kc_id=kc.id, action="edited", new_status="approved")


async def archive(
    session: AsyncSession,
    *,
    kc_id: uuid.UUID,
    expert_id: str,
    reason: str,
) -> KCReviewResult:
    """Expert archive → 'archived'。可用於 draft 或 approved 兩態。"""
    kc = (
        await session.execute(select(KnowledgeCard).where(KnowledgeCard.id == kc_id))
    ).scalar_one_or_none()
    if kc is None:
        raise KCReviewError(f"knowledge_card {kc_id} not found")
    if kc.status == "archived":
        raise KCReviewError(f"knowledge_card {kc_id} already archived")

    prev_status = kc.status
    kc.status = "archived"
    await session.flush()

    await audit.emit(
        session,
        event_type="kc.archived",
        tenant_id=kc.tenant_id,
        actor_id=expert_id,
        resource_type="knowledge_card",
        resource_id=str(kc.id),
        payload={"prev_status": prev_status, "reason": reason[:500]},
    )
    return KCReviewResult(kc_id=kc.id, action="archived", new_status="archived")


async def list_drafts(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID | None = None,
    limit: int = 50,
) -> list[dict[str, object]]:
    """列出 status='draft' 的 KnowledgeCard。"""
    sql = (
        "SELECT id, tenant_id, card_type, title, body_markdown, tags, "
        "       source_url, source_file_ref, created_at "
        "FROM knowledge_card WHERE status = 'draft' "
    )
    params: dict[str, object] = {"lim": limit}
    if tenant_id is not None:
        sql += "AND tenant_id = :tid "
        params["tid"] = str(tenant_id)
    sql += "ORDER BY created_at ASC LIMIT :lim"

    rows = (await session.execute(text(sql), params)).all()
    return [
        {
            "kc_id": str(row[0]),
            "tenant_id": str(row[1]),
            "card_type": row[2],
            "title": row[3],
            "body_markdown": row[4],
            "tags": list(row[5] or []),
            "source_url": row[6],
            "source_file_ref": row[7],
            "created_at": row[8].isoformat() if row[8] is not None else None,
        }
        for row in rows
    ]
