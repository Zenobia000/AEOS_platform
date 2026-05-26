"""CR-0001: skill_binding routing_rule + is_default + message.skill_version_id.

Revision ID: a1f2b3c40011
Revises: be692b03b553
Create Date: 2026-05-26

CR-0001-multi-vertical-framework.md §5 schema 變動：

1. skill_binding +1 column routing_rule JSONB NOT NULL DEFAULT '{}'
2. skill_binding +1 column is_default BOOLEAN NOT NULL DEFAULT false
3. skill_binding +partial UNIQUE idx (employee_id) WHERE is_default = true
   每 employee 至多 1 個 default fallback skill
4. message +1 column skill_version_id UUID NULL REFERENCES skill_version(id)
   記錄哪個 skill 處理了此 turn（audit + 多 vertical 統計）

Backfill: 既存 skill_binding row（demo seed 的 customer-service/faq-respond）
全部設 is_default=true → multi-skill routing 啟用前行為等同今日。
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "a1f2b3c40011"
down_revision = "be692b03b553"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── skill_binding: routing_rule + is_default ──
    op.add_column(
        "skill_binding",
        sa.Column(
            "routing_rule",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="hybrid router rule: {type, params, priority}; '{}' = match-all",
        ),
    )
    op.add_column(
        "skill_binding",
        sa.Column(
            "is_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="fallback skill when no routing_rule matches",
        ),
    )

    # 既存 row 全部設 is_default=true（每 employee 應只有 1 row in Phase 1 demo）
    op.execute(
        sa.text(
            """
            UPDATE skill_binding sb
            SET is_default = true
            WHERE id IN (
                SELECT DISTINCT ON (employee_id) id
                FROM skill_binding
                ORDER BY employee_id, created_at ASC
            )
            """
        )
    )

    # Partial unique idx：每 employee 至多 1 個 default
    op.create_index(
        "uq_skill_binding_default_per_emp",
        "skill_binding",
        ["employee_id"],
        unique=True,
        postgresql_where=sa.text("is_default = true"),
    )

    # ── message.skill_version_id ──
    op.add_column(
        "message",
        sa.Column(
            "skill_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="哪個 skill_version 處理了此 turn (CR-0001)",
        ),
    )
    # FK 不直接建（message 是 partition table，PG 限制不支援跨 partition FK；
    # 應用層保證一致 — 與 conversation_id 同 pattern，見 message.py line 47）


def downgrade() -> None:
    op.drop_column("message", "skill_version_id")
    op.drop_index("uq_skill_binding_default_per_emp", table_name="skill_binding")
    op.drop_column("skill_binding", "is_default")
    op.drop_column("skill_binding", "routing_rule")
