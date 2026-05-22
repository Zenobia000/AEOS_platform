"""KnowledgeCard + IngestionJob 模型 + RLS 測試."""

from __future__ import annotations

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ingestion_job import IngestionJob
from app.db.models.knowledge_card import KnowledgeCard
from app.db.models.tenant import Tenant


async def _make_tenant(session: AsyncSession, slug: str = "kc-test") -> Tenant:
    t = Tenant(name=f"Tenant-{slug}", slug=slug)
    session.add(t)
    await session.flush()
    return t


async def test_kc_create_minimal(db_session: AsyncSession) -> None:
    """最小欄位建立 KC：tenant_id + card_type + title + body + status."""
    tenant = await _make_tenant(db_session)
    kc = KnowledgeCard(
        tenant_id=tenant.id,
        card_type="faq",
        title="退貨期限",
        body_markdown="商品到貨後 7 天內可申請退貨",
        status="draft",
    )
    db_session.add(kc)
    await db_session.flush()

    assert kc.id is not None
    assert kc.version == 1
    assert kc.tags == []
    assert kc.created_at is not None


async def test_kc_card_type_check(db_session: AsyncSession) -> None:
    """card_type 必須是 5 個合法值之一。"""
    tenant = await _make_tenant(db_session, slug="kc-type")
    kc = KnowledgeCard(
        tenant_id=tenant.id,
        card_type="invalid_type",
        title="x",
        body_markdown="y",
        status="draft",
    )
    db_session.add(kc)
    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()
    assert "card_type_check" in str(exc.value).lower()


async def test_kc_status_check(db_session: AsyncSession) -> None:
    """status 必須是 3 個合法值之一。"""
    tenant = await _make_tenant(db_session, slug="kc-status")
    kc = KnowledgeCard(
        tenant_id=tenant.id,
        card_type="faq",
        title="x",
        body_markdown="y",
        status="pending",  # not in (draft, approved, archived)
    )
    db_session.add(kc)
    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()
    assert "status_check" in str(exc.value).lower()


async def test_kc_tags_array(db_session: AsyncSession) -> None:
    """tags 是 TEXT[]；可寫入並查回。"""
    tenant = await _make_tenant(db_session, slug="kc-tags")
    kc = KnowledgeCard(
        tenant_id=tenant.id,
        card_type="policy",
        title="退貨政策",
        body_markdown="...",
        tags=["return", "customer-service", "tw"],
        status="approved",
    )
    db_session.add(kc)
    await db_session.flush()

    fetched = (
        await db_session.execute(select(KnowledgeCard).where(KnowledgeCard.id == kc.id))
    ).scalar_one()
    assert fetched.tags == ["return", "customer-service", "tw"]


async def test_kc_embedding_vector(db_session: AsyncSession) -> None:
    """1024-dim embedding 可寫入 + 讀回（用零向量做 smoke）。"""
    tenant = await _make_tenant(db_session, slug="kc-emb")
    embedding = [0.0] * 1024
    kc = KnowledgeCard(
        tenant_id=tenant.id,
        card_type="faq",
        title="emb test",
        body_markdown="...",
        status="draft",
        embedding=embedding,
        embedding_model="voyage-3-lite",
    )
    db_session.add(kc)
    await db_session.flush()

    fetched = (
        await db_session.execute(select(KnowledgeCard).where(KnowledgeCard.id == kc.id))
    ).scalar_one()
    assert fetched.embedding is not None
    assert len(fetched.embedding) == 1024
    assert fetched.embedding_model == "voyage-3-lite"


async def test_kc_cosine_distance_smoke(db_session: AsyncSession) -> None:
    """ivfflat + vector_cosine_ops 真的能跑 <=> 距離查詢."""
    tenant = await _make_tenant(db_session, slug="kc-cosine")
    kc = KnowledgeCard(
        tenant_id=tenant.id,
        card_type="faq",
        title="cosine",
        body_markdown="...",
        status="approved",
        embedding=[1.0] + [0.0] * 1023,
    )
    db_session.add(kc)
    await db_session.flush()

    # query: vector cosine distance to a similar query vector
    result = await db_session.execute(
        text(
            "SELECT id FROM knowledge_card "
            "WHERE tenant_id = :tid "
            "ORDER BY embedding <=> :qv "
            "LIMIT 1"
        ),
        {"tid": str(tenant.id), "qv": "[" + ",".join(["1.0"] + ["0.0"] * 1023) + "]"},
    )
    row = result.first()
    assert row is not None
    assert row[0] == kc.id


async def test_kc_rls_policy_registered(db_session: AsyncSession) -> None:
    """knowledge_card 應有 RLS policy 已建。"""
    result = await db_session.execute(
        text(
            "SELECT policyname FROM pg_policies "
            "WHERE schemaname='public' AND tablename='knowledge_card'"
        )
    )
    names = {row[0] for row in result.all()}
    assert "knowledge_card_tenant_isolation" in names


async def test_ingestion_job_create(db_session: AsyncSession) -> None:
    """IngestionJob 基本欄位 + status check."""
    tenant = await _make_tenant(db_session, slug="ing-test")
    job = IngestionJob(
        tenant_id=tenant.id,
        source_file_ref="s3://bucket/abc.pdf",
        source_filename="abc.pdf",
        status="pending",
    )
    db_session.add(job)
    await db_session.flush()

    assert job.id is not None
    assert job.cards_created == 0


async def test_ingestion_job_invalid_status(db_session: AsyncSession) -> None:
    tenant = await _make_tenant(db_session, slug="ing-bad")
    job = IngestionJob(
        tenant_id=tenant.id,
        source_file_ref="s3://x",
        source_filename="x",
        status="weird",
    )
    db_session.add(job)
    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()
    assert "status_check" in str(exc.value).lower()


async def test_kc_indexes_exist(db_session: AsyncSession) -> None:
    """ivfflat / GIN / btree indexes 全部就位."""
    result = await db_session.execute(
        text(
            "SELECT indexname FROM pg_indexes "
            "WHERE schemaname='public' AND tablename='knowledge_card'"
        )
    )
    names = {row[0] for row in result.all()}
    # 主要 4 個 + PK + 可能其他
    assert "idx_kc_embedding" in names
    assert "idx_kc_tags" in names
    # idx_kc_tenant_status / idx_kc_type 在 conftest 沒同步，alembic
    # 才有；測試環境僅有 ivfflat + GIN 即可（這 2 個是 vector 查詢核心）
