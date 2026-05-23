"""knowledge_card + ingestion_job with pgvector and RLS

Revision ID: be041f897325
Revises: 774d543eb09a
Create Date: 2026-05-22

對應規格：
- db-schema.md §4.2 knowledge_card
- db-schema.md §4.3 ingestion_job
- MC-008 Knowledge RAG: 5 card_type + 3 status + pgvector(1024) ivfflat
- ADR-0007: 共享 PG + RLS + 應用層雙重檢查
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "be041f897325"
down_revision: str | Sequence[str] | None = "774d543eb09a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── ingestion_job ─────────────────────────────────
    op.create_table(
        "ingestion_job",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column(
            "source_file_ref", sa.Text(), nullable=False, comment="S3 path"
        ),
        sa.Column(
            "source_filename",
            sa.Text(),
            nullable=False,
            comment="original filename",
        ),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "cards_created",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name=op.f("ck_ingestion_job_status_check"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_ingestion_job_tenant_id_tenant"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingestion_job")),
    )
    # db-schema §4.3: idx_ingestion_tenant ON (tenant_id, created_at DESC)
    op.execute(
        "CREATE INDEX idx_ingestion_tenant "
        "ON ingestion_job (tenant_id, created_at DESC)"
    )

    # ── knowledge_card ────────────────────────────────
    op.create_table(
        "knowledge_card",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("card_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body_markdown", sa.Text(), nullable=False),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column(
            "source_file_ref",
            sa.Text(),
            nullable=True,
            comment="S3 path to original uploaded file",
        ),
        sa.Column(
            "version", sa.Integer(), server_default="1", nullable=False
        ),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("approved_by", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "embedding",
            Vector(1024),
            nullable=True,
            comment="pgvector embedding；voyage-3-lite or similar 1024-dim",
        ),
        sa.Column(
            "embedding_model",
            sa.Text(),
            nullable=True,
            comment="model 名稱用於 traceability",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "card_type IN ('faq', 'policy', 'product', 'procedure', 'risk')",
            name=op.f("ck_knowledge_card_card_type_check"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'approved', 'archived')",
            name=op.f("ck_knowledge_card_status_check"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_knowledge_card_tenant_id_tenant"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_card")),
    )
    # db-schema §4.2 indexes
    op.execute(
        "CREATE INDEX idx_kc_tenant_status "
        "ON knowledge_card (tenant_id, status)"
    )
    op.execute(
        "CREATE INDEX idx_kc_tags ON knowledge_card USING GIN (tags)"
    )
    op.execute(
        "CREATE INDEX idx_kc_embedding ON knowledge_card "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
    op.execute(
        "CREATE INDEX idx_kc_type ON knowledge_card (tenant_id, card_type)"
    )

    # ── RLS ───────────────────────────────────────────
    op.execute("ALTER TABLE knowledge_card ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY knowledge_card_tenant_isolation ON knowledge_card "
        "USING (tenant_id::text = current_setting('app.tenant_id', true))"
    )
    op.execute("ALTER TABLE ingestion_job ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY ingestion_job_tenant_isolation ON ingestion_job "
        "USING (tenant_id::text = current_setting('app.tenant_id', true))"
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS ingestion_job_tenant_isolation ON ingestion_job"
    )
    op.execute(
        "DROP POLICY IF EXISTS knowledge_card_tenant_isolation ON knowledge_card"
    )

    op.execute("DROP INDEX IF EXISTS idx_kc_type")
    op.execute("DROP INDEX IF EXISTS idx_kc_embedding")
    op.execute("DROP INDEX IF EXISTS idx_kc_tags")
    op.execute("DROP INDEX IF EXISTS idx_kc_tenant_status")
    op.drop_table("knowledge_card")

    op.execute("DROP INDEX IF EXISTS idx_ingestion_tenant")
    op.drop_table("ingestion_job")
