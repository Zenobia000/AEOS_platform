"""enable extensions + tenant/api_key/audit_log + RLS + audit append-only trigger

Revision ID: 774d543eb09a
Revises:
Create Date: 2026-05-22

對應規格：
- db-schema.md §1 命名: 單數表名 / 純 TEXT / TEXT+CHECK 取代 native enum
- db-schema.md §3 RLS: 共享 PG + RLS + 應用層雙重檢查（ADR-0007）
- db-schema.md §3.2 audit_log cross-tenant by design
- MC-001 Audit Service: append-only PG + trigger 防 UPDATE/DELETE
- MC-004 Tenant Manager: 4 態狀態機（pending/active/suspended/archived）
- ADR-0006 Auth: API Key (bcrypt) per-tenant
- SEC-001 §6.1 #4: RLS 啟用 + cross-tenant query 測試
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "774d543eb09a"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. 擴充功能 ─────────────────────────────────────
    # pgcrypto: gen_random_uuid() 與 crypt() 函式
    # vector:   pgvector embedding（給後續 KC 表用）
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── 2. tenant（aggregate root，無外鍵）──────────────
    # status 用 TEXT + CHECK constraint（依 db-schema.md §1 line 24，不用 native enum）
    op.create_table(
        "tenant",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'pending'"),
            nullable=False,
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
            "status IN ('pending', 'active', 'suspended', 'archived')",
            name=op.f("ck_tenant_status_check"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tenant")),
        sa.UniqueConstraint("slug", name=op.f("uq_tenant_slug")),
    )

    # ── 3. api_key（FK -> tenant）─────────────────────
    op.create_table(
        "api_key",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("key_hash", sa.Text(), nullable=False),
        sa.Column("last_four", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_api_key_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_api_key")),
        sa.UniqueConstraint("key_hash", name=op.f("uq_api_key_key_hash")),
    )
    op.create_index(
        op.f("ix_api_key_tenant_id"),
        "api_key",
        ["tenant_id"],
        unique=False,
    )

    # ── 4. audit_log（append-only；tenant_id 可 NULL；cross-tenant by design）──
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column(
            "actor_id",
            sa.Text(),
            nullable=True,
            comment="操作者：tenant admin user id / api_key id / 'system'",
        ),
        sa.Column(
            "event_type",
            sa.Text(),
            nullable=False,
            comment="e.g. tenant.created, skill.promoted, ai.draft_generated",
        ),
        sa.Column("resource_type", sa.Text(), nullable=True),
        sa.Column("resource_id", sa.Text(), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_log")),
    )
    op.create_index(
        "ix_audit_log_event_type",
        "audit_log",
        ["event_type", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_log_resource",
        "audit_log",
        ["resource_type", "resource_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_log_tenant_occurred",
        "audit_log",
        ["tenant_id", "occurred_at"],
        unique=False,
    )

    # ── 5. Append-only trigger on audit_log ────────────
    # 任何 UPDATE / DELETE 都 raise；只允許 INSERT
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_log_block_modify()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION
                'audit_log is append-only; % is not allowed', TG_OP
                USING ERRCODE = 'insufficient_privilege';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_log_block_update
        BEFORE UPDATE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION audit_log_block_modify();
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_log_block_delete
        BEFORE DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION audit_log_block_modify();
        """
    )

    # ── 6. RLS（依 ADR-0007 / db-schema §3）────────────
    # tenant 表自己：用 id 作為 RLS key（每個 tenant 只看到自己）
    op.execute("ALTER TABLE tenant ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_self_isolation ON tenant
        USING (
            id::text = current_setting('app.tenant_id', true)
        )
        """
    )

    # api_key: tenant_id 作為 RLS key
    op.execute("ALTER TABLE api_key ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY api_key_tenant_isolation ON api_key
        USING (
            tenant_id::text = current_setting('app.tenant_id', true)
        )
        """
    )

    # audit_log: 同 RLS（tenant_id 為 NULL 的系統事件僅 BYPASSRLS 可見）
    op.execute("ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY audit_log_tenant_isolation ON audit_log
        USING (
            tenant_id IS NULL
            OR tenant_id::text = current_setting('app.tenant_id', true)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS audit_log_tenant_isolation ON audit_log")
    op.execute("DROP POLICY IF EXISTS api_key_tenant_isolation ON api_key")
    op.execute("DROP POLICY IF EXISTS tenant_self_isolation ON tenant")

    op.execute("DROP TRIGGER IF EXISTS audit_log_block_delete ON audit_log")
    op.execute("DROP TRIGGER IF EXISTS audit_log_block_update ON audit_log")
    op.execute("DROP FUNCTION IF EXISTS audit_log_block_modify()")

    op.drop_index("ix_audit_log_tenant_occurred", table_name="audit_log")
    op.drop_index("ix_audit_log_resource", table_name="audit_log")
    op.drop_index("ix_audit_log_event_type", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index(op.f("ix_api_key_tenant_id"), table_name="api_key")
    op.drop_table("api_key")
    op.drop_table("tenant")
