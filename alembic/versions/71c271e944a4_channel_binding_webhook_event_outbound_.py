"""channel_binding + webhook_event + outbound_message (MC-011)

Revision ID: 71c271e944a4
Revises: 89c67361deb1
Create Date: 2026-05-22

對應規格：
- db-schema.md §4.7~§4.9 Channel Gateway
- MC-011 Channel Gateway (LINE webhook + outbound)
- API-002 LINE webhook (dedup via webhook_event)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "71c271e944a4"
down_revision: str | Sequence[str] | None = "89c67361deb1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── channel_binding ────────────────────────────
    op.create_table(
        "channel_binding",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "channel IN ('line', 'web_chat', 'whatsapp')",
            name=op.f("ck_channel_binding_channel_check"),
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employee.id"],
            name=op.f("fk_channel_binding_employee_id_employee"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_channel_binding")),
    )
    op.create_index(
        "idx_channel_binding_emp_chan",
        "channel_binding",
        ["employee_id", "channel"],
        unique=True,
    )

    # ── webhook_event ──────────────────────────────
    op.create_table(
        "webhook_event",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", "channel", name="pk_webhook_event"),
    )
    op.create_index(
        "idx_webhook_event_purge",
        "webhook_event",
        ["received_at"],
    )

    # ── outbound_message ───────────────────────────
    op.create_table(
        "outbound_message",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("message_id", sa.UUID(), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("channel_user_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "retry_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "channel IN ('line', 'web_chat', 'whatsapp')",
            name=op.f("ck_outbound_message_channel_check"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'sent', 'failed', 'retrying')",
            name=op.f("ck_outbound_message_status_check"),
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversation.id"],
            name=op.f("fk_outbound_message_conversation_id_conversation"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_outbound_message_tenant_id_tenant"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_outbound_message")),
    )
    op.execute(
        "CREATE INDEX idx_outbound_pending ON outbound_message "
        "(status, created_at) WHERE status IN ('pending', 'retrying')"
    )

    # ── RLS ────────────────────────────────────────
    # channel_binding: 透過 employee join 限制（無直接 tenant_id 欄位）—
    # 與 message / conversation_handoff 同模式採 ALL allow
    op.execute("ALTER TABLE channel_binding ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY channel_binding_allow_all ON channel_binding USING (true)"
    )

    # webhook_event: 跨 tenant by design（webhook 入口層，未識別 tenant 前先寫）
    op.execute("ALTER TABLE webhook_event ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY webhook_event_allow_all ON webhook_event USING (true)"
    )

    # outbound_message: tenant_id 為 RLS key
    op.execute("ALTER TABLE outbound_message ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY outbound_message_tenant_isolation ON outbound_message "
        "USING (tenant_id::text = current_setting('app.tenant_id', true))"
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS outbound_message_tenant_isolation ON outbound_message"
    )
    op.execute("DROP POLICY IF EXISTS webhook_event_allow_all ON webhook_event")
    op.execute(
        "DROP POLICY IF EXISTS channel_binding_allow_all ON channel_binding"
    )

    op.execute("DROP INDEX IF EXISTS idx_outbound_pending")
    op.drop_table("outbound_message")

    op.drop_index("idx_webhook_event_purge", table_name="webhook_event")
    op.drop_table("webhook_event")

    op.drop_index("idx_channel_binding_emp_chan", table_name="channel_binding")
    op.drop_table("channel_binding")
