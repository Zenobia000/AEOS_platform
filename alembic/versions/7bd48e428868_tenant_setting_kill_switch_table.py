"""tenant_setting kill switch table

Revision ID: 7bd48e428868
Revises: 5c56148236b0
Create Date: 2026-05-22

對應 PRD-001 §5.5 emergency kill switch (UF-004):
- per-tenant ai_enabled boolean
- 預設 true；操作經 admin API set false
- DraftProcessor 每 turn 查 DB（< 1ms），30 秒內生效
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "7bd48e428868"
down_revision: str | Sequence[str] | None = "5c56148236b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenant_setting",
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "ai_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "disabled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("disabled_by", sa.Text(), nullable=True),
        sa.Column("disable_reason", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.execute("ALTER TABLE tenant_setting ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_setting_tenant_isolation ON tenant_setting "
        "USING (tenant_id::text = current_setting('app.tenant_id', true))"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_setting_tenant_isolation ON tenant_setting")
    op.drop_table("tenant_setting")
