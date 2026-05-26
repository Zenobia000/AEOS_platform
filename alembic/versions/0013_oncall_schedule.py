"""oncall_schedule — 第 25 張表（DB schema 25/25 收尾）.

Revision ID: c3d4e5f60013
Revises: b2c3d4e50012
Create Date: 2026-05-26

Phase 1 後續 #17 — 25 張表的最後一張。
對應 PRD-001 §5.5 + RUNBOOK-001 + SEC-001 §6.1 #12 incident drill。

設計：
- 每 tenant 維護一份 oncall 班表（per week / day rotation）
- expert_id NULL 表示「無人值班」（fallback to default channel）
- primary / secondary 兩階 escalation
- 真實接 PagerDuty 後，本表變成 PagerDuty schedule 的鏡像 / cache
- Phase 1 可手動維護；Phase 2 由 PagerDuty API sync

不在 Phase 1：
- 自動輪班生成（PagerDuty 來做）
- 排班衝突演算法
- 國定假日對應
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "c3d4e5f60013"
down_revision = "b2c3d4e50012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "oncall_schedule",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "shift_start",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="班次開始時間（UTC）",
        ),
        sa.Column(
            "shift_end",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="班次結束時間（UTC）",
        ),
        sa.Column(
            "primary_expert_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="主值班 expert（NULL = 無人值班 fallback default channel）",
        ),
        sa.Column(
            "secondary_expert_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="副值班（primary 沒回應 escalate）",
        ),
        sa.Column(
            "pagerduty_schedule_id",
            sa.Text(),
            nullable=True,
            comment="對應 PagerDuty schedule ID（Phase 2 sync）",
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.CheckConstraint(
            "shift_end > shift_start",
            name="oncall_schedule_time_range_check",
        ),
    )
    # idx for 「找此時刻誰值班」query
    op.create_index(
        "idx_oncall_schedule_tenant_shift",
        "oncall_schedule",
        ["tenant_id", "shift_start", "shift_end"],
    )
    op.execute("ALTER TABLE oncall_schedule ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("ALTER TABLE oncall_schedule DISABLE ROW LEVEL SECURITY")
    op.drop_index("idx_oncall_schedule_tenant_shift", table_name="oncall_schedule")
    op.drop_table("oncall_schedule")
