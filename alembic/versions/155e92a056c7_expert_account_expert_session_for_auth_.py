"""expert_account + expert_session for auth (S5)

Revision ID: 155e92a056c7
Revises: 9575402d6485
Create Date: 2026-05-23

對應 S5 §MFA / auth — Expert Console pilot 上線 hard gate:
- expert_account: 內部 expert (跨 tenant 可用) — email + bcrypt password +
  role + tenant_id (NULL = platform admin, 否則限該 tenant)
- expert_session: token-based session (token PK, expires_at + last_used)

Phase 1 不接 TOTP MFA；Phase 2 加 expert_mfa_secret 表升級。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "155e92a056c7"
down_revision: str | Sequence[str] | None = "9575402d6485"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "expert_account",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False, server_default=sa.text("'expert'")),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant.id", ondelete="CASCADE"),
            nullable=True,
            comment="NULL = platform admin; 否則限該 tenant scope",
        ),
        sa.Column(
            "enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint(
            "role IN ('expert', 'admin')", name="expert_account_role_check"
        ),
    )
    op.create_index(
        "idx_expert_account_email", "expert_account", ["email"], unique=True
    )

    op.create_table(
        "expert_session",
        sa.Column("token", sa.Text(), primary_key=True),
        sa.Column(
            "expert_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("expert_account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_expert_session_expert", "expert_session", ["expert_id"])


def downgrade() -> None:
    op.drop_table("expert_session")
    op.drop_table("expert_account")
