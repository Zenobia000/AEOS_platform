"""employee + conversation + message partitioned + handoff

Revision ID: 7b2dc371f434
Revises: be041f897325
Create Date: 2026-05-22

對應規格：
- db-schema.md §4.1 employee
- db-schema.md §4.4 conversation (6 態 status, 4 種 outcome)
- db-schema.md §4.5 message (PARTITION BY RANGE created_at, 月分區)
- db-schema.md §4.6 conversation_handoff
- MC-009 Employee Runtime (Frozen Runtime snapshot)
- MC-010 Conversation Engine
- ADR-0005 PII pseudonymize
- ADR-0007 共享 PG + RLS
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7b2dc371f434"
down_revision: str | Sequence[str] | None = "be041f897325"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── employee ──────────────────────────────────────
    op.create_table(
        "employee",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "role",
            sa.Text(),
            nullable=False,
            comment="'customer_service' (Phase 1)",
        ),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "version",
            sa.Text(),
            nullable=False,
            comment="semver snapshot",
        ),
        sa.Column(
            "persona_config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
            comment="{ tone, style, language, greeting }",
        ),
        sa.Column(
            "runtime_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
            comment="frozen config: skill_bindings, tool_bindings, llm_config",
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
            "status IN ('draft', 'live', 'paused', 'retired')",
            name=op.f("ck_employee_status_check"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_employee_tenant_id_tenant"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee")),
    )
    op.create_index(
        "idx_employee_tenant", "employee", ["tenant_id"], unique=False
    )
    op.create_index(
        "idx_employee_status",
        "employee",
        ["tenant_id", "status"],
        unique=False,
    )

    # ── conversation ──────────────────────────────────
    op.create_table(
        "conversation",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column(
            "employee_version",
            sa.Text(),
            nullable=False,
            comment="snapshot version at conversation start",
        ),
        sa.Column(
            "end_user_pseudo_id",
            sa.Text(),
            nullable=False,
            comment="pseudonymized (ADR-0005)",
        ),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column(
            "channel_user_id",
            sa.Text(),
            nullable=False,
            comment="channel-specific user ID (hashed)",
        ),
        sa.Column(
            "status",
            sa.Text(),
            server_default="open",
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_message_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="for idle timeout detection",
        ),
        sa.Column(
            "ended_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("outcome", sa.Text(), nullable=True),
        sa.Column(
            "summary",
            sa.Text(),
            nullable=True,
            comment="L2.5 session summary (generated on close)",
        ),
        sa.Column(
            "message_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
            comment="denormalized counter",
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.CheckConstraint(
            "channel IN ('line', 'web_chat', 'whatsapp')",
            name=op.f("ck_conversation_channel_check"),
        ),
        sa.CheckConstraint(
            "status IN ('open', 'active', 'waiting_human', "
            "'resolved', 'closed', 'archived')",
            name=op.f("ck_conversation_status_check"),
        ),
        sa.CheckConstraint(
            "outcome IS NULL OR outcome IN ("
            "'resolved', 'handoff_human', 'abandoned', 'error')",
            name=op.f("ck_conversation_outcome_check"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_conversation_tenant_id_tenant"),
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employee.id"],
            name=op.f("fk_conversation_employee_id_employee"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation")),
    )
    op.execute(
        "CREATE INDEX idx_conv_tenant_started "
        "ON conversation (tenant_id, started_at DESC)"
    )
    op.create_index("idx_conv_employee", "conversation", ["employee_id"])
    op.create_index(
        "idx_conv_status", "conversation", ["tenant_id", "status"]
    )
    op.create_index(
        "idx_conv_end_user",
        "conversation",
        ["tenant_id", "end_user_pseudo_id"],
    )
    op.execute(
        "CREATE INDEX idx_conv_idle ON conversation (status, last_message_at) "
        "WHERE status IN ('open', 'active', 'waiting_human')"
    )

    # ── message (partitioned by month on created_at) ──
    op.execute(
        """
        CREATE TABLE message (
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            conversation_id UUID NOT NULL,
            seq INT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            content_raw_ref UUID,
            skill_invocation_id UUID,
            tool_invocations JSONB NOT NULL DEFAULT '[]',
            token_count INT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id, created_at),
            UNIQUE (conversation_id, seq, created_at),
            CONSTRAINT ck_message_role_check CHECK (
                role IN ('user', 'assistant', 'tool', 'system')
            )
        ) PARTITION BY RANGE (created_at);
        """
    )
    # 為現有月份 + 接下來 6 個月建 partition（Phase 1 手動；Phase 2 自動 cron）
    # 2026-05 ~ 2026-12 涵蓋 Phase 1 全期
    for year, month in [
        (2026, 5),
        (2026, 6),
        (2026, 7),
        (2026, 8),
        (2026, 9),
        (2026, 10),
        (2026, 11),
        (2026, 12),
    ]:
        next_year = year if month < 12 else year + 1
        next_month = month + 1 if month < 12 else 1
        op.execute(
            f"CREATE TABLE message_{year}_{month:02d} "
            f"PARTITION OF message "
            f"FOR VALUES FROM ('{year}-{month:02d}-01') "
            f"TO ('{next_year}-{next_month:02d}-01');"
        )

    # ── conversation_handoff ─────────────────────────
    op.create_table(
        "conversation_handoff",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("from_conversation_id", sa.UUID(), nullable=False),
        sa.Column(
            "to_conversation_id",
            sa.UUID(),
            nullable=True,
            comment="NULL until Expert picks up",
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "handoff_message",
            sa.Text(),
            nullable=True,
            comment="context for Expert",
        ),
        sa.Column(
            "expert_id",
            sa.Text(),
            nullable=True,
            comment="who picked up",
        ),
        sa.Column(
            "picked_up_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "resolved_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "reason IN ('low_confidence', 'restricted_tool', "
            "'user_request', 'policy_deny')",
            name=op.f("ck_conversation_handoff_reason_check"),
        ),
        sa.ForeignKeyConstraint(
            ["from_conversation_id"],
            ["conversation.id"],
            name=op.f(
                "fk_conversation_handoff_from_conversation_id_conversation"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "id", name=op.f("pk_conversation_handoff")
        ),
    )
    op.execute(
        "CREATE INDEX idx_handoff_pending ON conversation_handoff (created_at) "
        "WHERE to_conversation_id IS NULL"
    )

    # ── RLS ───────────────────────────────────────────
    for tbl in (
        "employee",
        "conversation",
        "message",
        "conversation_handoff",
    ):
        op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY")

    op.execute(
        "CREATE POLICY employee_tenant_isolation ON employee "
        "USING (tenant_id::text = current_setting('app.tenant_id', true))"
    )
    op.execute(
        "CREATE POLICY conversation_tenant_isolation ON conversation "
        "USING (tenant_id::text = current_setting('app.tenant_id', true))"
    )
    # message 表沒有 tenant_id；透過 conversation join 控制可見性
    # 為了簡化 + 維持 partition 效能，message 表的 RLS 是 ALL 允許
    # （隔離由應用層 join + conversation RLS 保證）
    op.execute(
        "CREATE POLICY message_allow_all ON message USING (true)"
    )
    # conversation_handoff 透過 from_conversation_id 的 conversation 隔離；
    # 為簡化採同樣 ALL 允許（隔離由 join 保證）
    op.execute(
        "CREATE POLICY conversation_handoff_allow_all "
        "ON conversation_handoff USING (true)"
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS conversation_handoff_allow_all "
        "ON conversation_handoff"
    )
    op.execute("DROP POLICY IF EXISTS message_allow_all ON message")
    op.execute(
        "DROP POLICY IF EXISTS conversation_tenant_isolation ON conversation"
    )
    op.execute(
        "DROP POLICY IF EXISTS employee_tenant_isolation ON employee"
    )

    op.execute("DROP INDEX IF EXISTS idx_handoff_pending")
    op.drop_table("conversation_handoff")

    # drop message partitions + parent
    for year, month in [
        (2026, 5),
        (2026, 6),
        (2026, 7),
        (2026, 8),
        (2026, 9),
        (2026, 10),
        (2026, 11),
        (2026, 12),
    ]:
        op.execute(f"DROP TABLE IF EXISTS message_{year}_{month:02d}")
    op.drop_table("message")

    op.execute("DROP INDEX IF EXISTS idx_conv_idle")
    op.drop_index("idx_conv_end_user", table_name="conversation")
    op.drop_index("idx_conv_status", table_name="conversation")
    op.drop_index("idx_conv_employee", table_name="conversation")
    op.execute("DROP INDEX IF EXISTS idx_conv_tenant_started")
    op.drop_table("conversation")

    op.drop_index("idx_employee_status", table_name="employee")
    op.drop_index("idx_employee_tenant", table_name="employee")
    op.drop_table("employee")
