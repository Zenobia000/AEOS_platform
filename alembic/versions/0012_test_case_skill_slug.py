"""test_case +skill_slug (multi-vertical testset filter).

Revision ID: b2c3d4e50012
Revises: a1f2b3c40011
Create Date: 2026-05-26

Phase 1 後續 #23 — multi-vertical 期，testset 題庫要能按 skill_slug 區隔。
新加 test_case.skill_slug TEXT NULL（NULL = 通用題；既存題不動）。

不破壞 backward compat：
- 既存 row 全部 skill_slug=NULL
- API ?skill_slug= 未提供 → 不 filter（行為等同 pre-CR）
- API ?skill_slug=xxx → 只列該 skill + NULL 通用題
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "b2c3d4e50012"
down_revision = "a1f2b3c40011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "test_case",
        sa.Column(
            "skill_slug",
            sa.Text(),
            nullable=True,
            comment="vertical/skill scope; NULL = 通用題（CR-0001 多 vertical 後加）",
        ),
    )
    # 加 partial index 給 ?skill_slug= 查詢
    op.create_index(
        "idx_test_case_skill_slug",
        "test_case",
        ["tenant_id", "skill_slug"],
        postgresql_where=sa.text("skill_slug IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_test_case_skill_slug", table_name="test_case")
    op.drop_column("test_case", "skill_slug")
