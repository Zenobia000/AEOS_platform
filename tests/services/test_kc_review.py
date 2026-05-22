"""KCReview service 單元測試 — approve / edit / archive / list_drafts."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog
from app.db.models.knowledge_card import KnowledgeCard
from app.db.models.tenant import Tenant
from app.services import kc_review


async def _seed_draft(
    session: AsyncSession,
    *,
    title: str = "退貨政策",
    body: str = "本店退貨期限為到貨後 7 天內，請保留發票",
    card_type: str = "policy",
    tags: list[str] | None = None,
    slug_suffix: str = "kc",
) -> tuple[Tenant, KnowledgeCard]:
    tenant = Tenant(name="Acme", slug=f"acme-{uuid.uuid4().hex[:6]}-{slug_suffix}")
    session.add(tenant)
    await session.flush()
    kc = KnowledgeCard(
        tenant_id=tenant.id,
        card_type=card_type,
        title=title,
        body_markdown=body,
        tags=tags or ["退貨"],
        status="draft",
    )
    session.add(kc)
    await session.flush()
    return tenant, kc


async def test_approve_marks_approved_and_sets_approved_by(
    db_session: AsyncSession,
) -> None:
    _, kc = await _seed_draft(db_session, slug_suffix="appv")
    result = await kc_review.approve(db_session, kc_id=kc.id, expert_id="expert-jenny")
    assert result.action == "approved"
    assert result.new_status == "approved"

    refreshed = (
        await db_session.execute(select(KnowledgeCard).where(KnowledgeCard.id == kc.id))
    ).scalar_one()
    assert refreshed.status == "approved"
    assert refreshed.approved_by == "expert-jenny"
    assert refreshed.approved_at is not None

    audit_row = (
        await db_session.execute(select(AuditLog).where(AuditLog.event_type == "kc.draft_approved"))
    ).scalar_one()
    assert audit_row.actor_id == "expert-jenny"


async def test_edit_updates_fields_and_approves(db_session: AsyncSession) -> None:
    _, kc = await _seed_draft(db_session, slug_suffix="edit")
    new_title = "退貨政策（小編修訂）"
    new_body = "本店退貨期限為到貨後 14 天內申請；請保留發票與包裝完整"
    new_tags = ["退貨", "政策", "修訂"]

    result = await kc_review.edit_and_approve(
        db_session,
        kc_id=kc.id,
        expert_id="expert-amy",
        title=new_title,
        body_markdown=new_body,
        tags=new_tags,
        card_type="faq",
    )
    assert result.action == "edited"
    assert result.new_status == "approved"

    refreshed = (
        await db_session.execute(select(KnowledgeCard).where(KnowledgeCard.id == kc.id))
    ).scalar_one()
    assert refreshed.title == new_title
    assert refreshed.body_markdown == new_body
    assert list(refreshed.tags) == new_tags
    assert refreshed.card_type == "faq"
    assert refreshed.status == "approved"
    assert refreshed.approved_by == "expert-amy"

    audit_row = (
        await db_session.execute(select(AuditLog).where(AuditLog.event_type == "kc.draft_edited"))
    ).scalar_one()
    changes = audit_row.payload["changes"]
    assert "title" in changes
    assert "card_type" in changes
    assert changes["card_type"] == "faq"


async def test_archive_marks_archived(db_session: AsyncSession) -> None:
    _, kc = await _seed_draft(db_session, slug_suffix="arch")
    result = await kc_review.archive(
        db_session,
        kc_id=kc.id,
        expert_id="expert-ben",
        reason="重複內容；已被另一張取代",
    )
    assert result.action == "archived"
    assert result.new_status == "archived"

    refreshed = (
        await db_session.execute(select(KnowledgeCard).where(KnowledgeCard.id == kc.id))
    ).scalar_one()
    assert refreshed.status == "archived"

    audit_row = (
        await db_session.execute(select(AuditLog).where(AuditLog.event_type == "kc.archived"))
    ).scalar_one()
    assert audit_row.payload["prev_status"] == "draft"
    assert "重複" in audit_row.payload["reason"]


async def test_archive_can_handle_approved_kc(db_session: AsyncSession) -> None:
    """已 approved 的 KC 也能被 archive（治理：合規退役）。"""
    _, kc = await _seed_draft(db_session, slug_suffix="arch2")
    kc.status = "approved"
    await db_session.flush()

    result = await kc_review.archive(db_session, kc_id=kc.id, expert_id="x", reason="法律變更")
    assert result.new_status == "archived"


async def test_archive_already_archived_raises(db_session: AsyncSession) -> None:
    _, kc = await _seed_draft(db_session, slug_suffix="arch3")
    kc.status = "archived"
    await db_session.flush()

    with pytest.raises(kc_review.KCReviewError, match="already archived"):
        await kc_review.archive(db_session, kc_id=kc.id, expert_id="x", reason="r")


async def test_approve_wrong_status_raises(db_session: AsyncSession) -> None:
    _, kc = await _seed_draft(db_session, slug_suffix="wrong")
    kc.status = "approved"
    await db_session.flush()

    with pytest.raises(kc_review.KCReviewError, match="not in draft"):
        await kc_review.approve(db_session, kc_id=kc.id, expert_id="x")


async def test_approve_unknown_raises(db_session: AsyncSession) -> None:
    with pytest.raises(kc_review.KCReviewError, match="not found"):
        await kc_review.approve(db_session, kc_id=uuid.uuid4(), expert_id="x")


async def test_edit_no_field_raises(db_session: AsyncSession) -> None:
    _, kc = await _seed_draft(db_session, slug_suffix="nofield")
    with pytest.raises(kc_review.KCReviewError, match="at least one"):
        await kc_review.edit_and_approve(db_session, kc_id=kc.id, expert_id="x")


async def test_edit_invalid_card_type_raises(db_session: AsyncSession) -> None:
    _, kc = await _seed_draft(db_session, slug_suffix="bad-ct")
    with pytest.raises(kc_review.KCReviewError, match="card_type"):
        await kc_review.edit_and_approve(
            db_session,
            kc_id=kc.id,
            expert_id="x",
            card_type="nonsense",
        )


async def test_edit_empty_title_raises(db_session: AsyncSession) -> None:
    _, kc = await _seed_draft(db_session, slug_suffix="empty-t")
    with pytest.raises(kc_review.KCReviewError, match="title"):
        await kc_review.edit_and_approve(
            db_session,
            kc_id=kc.id,
            expert_id="x",
            title="   ",
        )


async def test_list_drafts_filters_status(db_session: AsyncSession) -> None:
    tenant, kc = await _seed_draft(db_session, slug_suffix="list1")
    items = await kc_review.list_drafts(db_session, tenant_id=tenant.id)
    assert len(items) == 1
    item = items[0]
    assert item["kc_id"] == str(kc.id)
    assert item["card_type"] == "policy"
    tags = item["tags"]
    assert isinstance(tags, list)
    assert "退貨" in tags


async def test_list_drafts_excludes_approved(db_session: AsyncSession) -> None:
    tenant, kc = await _seed_draft(db_session, slug_suffix="list2")
    kc.status = "approved"
    await db_session.flush()

    items = await kc_review.list_drafts(db_session, tenant_id=tenant.id)
    assert items == []
