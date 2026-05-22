"""test_case + test_run + test_run_case for S3 TestSet & Skill v1.0

Revision ID: 9575402d6485
Revises: 7bd48e428868
Create Date: 2026-05-22

對應 PRD-001 §5.2 F-TS-* + AC-001 pass rate ≥ 0.80 measurement.

3 表結構：
- test_case：tenant 內的單一測試題（user_input + expected_outcome
  + expected_keywords 關鍵字白名單）
- test_run：一次批次跑（綁定 skill_slug + skill_version snapshot）
- test_run_case：composite PK；單一 case 在 single run 的執行結果
  + judge_score（0~1）+ judge_reason
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "9575402d6485"
down_revision: str | Sequence[str] | None = "7bd48e428868"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── test_case ──────────────────────────────────
    op.create_table(
        "test_case",
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
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("user_input", sa.Text(), nullable=False),
        sa.Column("expected_outcome", sa.Text(), nullable=False),
        sa.Column(
            "expected_keywords",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_test_case_tenant", "test_case", ["tenant_id", "enabled"])
    op.execute("ALTER TABLE test_case ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY test_case_tenant_isolation ON test_case "
        "USING (tenant_id::text = current_setting('app.tenant_id', true))"
    )

    # ── test_run ──────────────────────────────────
    op.create_table(
        "test_run",
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
        sa.Column("skill_slug", sa.Text(), nullable=False),
        sa.Column("skill_version", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "total_cases", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "passed_cases", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "failed_cases", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "pass_rate",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="test_run_status_check",
        ),
    )
    op.create_index("idx_test_run_tenant", "test_run", ["tenant_id", "created_at"])
    op.execute("ALTER TABLE test_run ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY test_run_tenant_isolation ON test_run "
        "USING (tenant_id::text = current_setting('app.tenant_id', true))"
    )

    # ── test_run_case ─────────────────────────────
    op.create_table(
        "test_run_case",
        sa.Column(
            "test_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("test_run.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "test_case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("test_case.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("actual_output", sa.Text(), nullable=True),
        sa.Column("judge_score", sa.Float(), nullable=True),
        sa.Column("judge_reason", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'passed', 'failed', 'error')",
            name="test_run_case_status_check",
        ),
    )


def downgrade() -> None:
    op.drop_table("test_run_case")
    op.execute("DROP POLICY IF EXISTS test_run_tenant_isolation ON test_run")
    op.drop_table("test_run")
    op.execute("DROP POLICY IF EXISTS test_case_tenant_isolation ON test_case")
    op.drop_table("test_case")
