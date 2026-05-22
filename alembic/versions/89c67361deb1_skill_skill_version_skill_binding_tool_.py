"""skill + skill_version + skill_binding + tool + tool_invocation + tool_policy

Revision ID: 89c67361deb1
Revises: 7b2dc371f434
Create Date: 2026-05-22

對應規格：
- db-schema.md §3.1~§3.6 Control Plane
- MC-005 Skill Registry (skill / skill_version / skill_binding)
- MC-006 Tool Registry (tool / tool_invocation / tool_policy)
- ADR-0003 Git monorepo + YAML manifest（DB 為查詢鏡像）
- ADR-0007 共享 PG + RLS
- skill_version production quality gate: pass_rate >= 0.80 + approved（DB CHECK）
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "89c67361deb1"
down_revision: str | Sequence[str] | None = "7b2dc371f434"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. skill ──────────────────────────────────────
    op.create_table(
        "skill",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.UUID(),
            nullable=True,
            comment="NULL = platform-level skill (Phase 2)",
        ),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("vertical", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner", sa.Text(), nullable=True),
        sa.Column(
            "current_production_version",
            sa.Text(),
            nullable=True,
            comment="semver",
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
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name=op.f("fk_skill_tenant_id_tenant")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skill")),
    )
    # db-schema §3.1 unique partial index (COALESCE 處理 NULL tenant_id)
    op.execute(
        "CREATE UNIQUE INDEX idx_skill_tenant_slug ON skill "
        "(COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid), slug)"
    )

    # ── 2. skill_version ──────────────────────────────
    op.create_table(
        "skill_version",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Text(),
            server_default="draft",
            nullable=False,
        ),
        sa.Column("prompt_template_ref", sa.Text(), nullable=False),
        sa.Column(
            "io_contract",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "tool_bindings",
            postgresql.ARRAY(sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "policy_refs",
            postgresql.ARRAY(sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("test_set_ref", sa.Text(), nullable=True),
        sa.Column(
            "test_pass_rate",
            sa.Numeric(precision=5, scale=4),
            nullable=True,
        ),
        sa.Column(
            "quality_gate_scores",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("approved_by", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deprecated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("git_commit_sha", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'testing', 'approved', 'production', 'deprecated')",
            name=op.f("ck_skill_version_status_check"),
        ),
        # MC-005 production Quality Gate
        sa.CheckConstraint(
            "(status <> 'production') OR "
            "(approved_by IS NOT NULL AND approved_at IS NOT NULL "
            "AND test_pass_rate >= 0.80)",
            name=op.f("ck_skill_version_production_quality_gate"),
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skill.id"],
            name=op.f("fk_skill_version_skill_id_skill"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_skill_version_tenant_id_tenant"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skill_version")),
        sa.UniqueConstraint(
            "skill_id", "version", name="uq_skill_version_skill_version"
        ),
    )
    op.create_index(
        "idx_skill_version_skill_version",
        "skill_version",
        ["skill_id", "version"],
    )
    op.create_index(
        "idx_skill_version_tenant_status",
        "skill_version",
        ["tenant_id", "status"],
    )

    # ── 3. skill_binding ──────────────────────────────
    op.create_table(
        "skill_binding",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("skill_version_id", sa.UUID(), nullable=False),
        sa.Column(
            "priority",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employee.id"],
            name=op.f("fk_skill_binding_employee_id_employee"),
        ),
        sa.ForeignKeyConstraint(
            ["skill_version_id"],
            ["skill_version.id"],
            name=op.f("fk_skill_binding_skill_version_id_skill_version"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_skill_binding_tenant_id_tenant"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skill_binding")),
    )
    op.create_index(
        "idx_skill_binding_emp_sv",
        "skill_binding",
        ["employee_id", "skill_version_id"],
        unique=True,
    )

    # ── 4. tool ───────────────────────────────────────
    op.create_table(
        "tool",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.UUID(),
            nullable=True,
            comment="NULL = system built-in tool",
        ),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("tool_type", sa.Text(), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=True),
        sa.Column("auth_method", sa.Text(), nullable=True),
        sa.Column(
            "auth_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "input_schema",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "output_schema",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "risk_tier",
            sa.Text(),
            server_default="safe",
            nullable=False,
        ),
        sa.Column(
            "rate_limit_rpm",
            sa.Integer(),
            server_default="60",
            nullable=False,
        ),
        sa.Column(
            "timeout_ms",
            sa.Integer(),
            server_default="5000",
            nullable=False,
        ),
        sa.Column(
            "retry_policy",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default='{"max_retries": 2, "backoff_ms": 500}',
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "tool_type IN ('internal', 'http_api', 'db_query', 'function')",
            name=op.f("ck_tool_tool_type_check"),
        ),
        sa.CheckConstraint(
            "auth_method IS NULL OR auth_method IN "
            "('none', 'api_key', 'bearer', 'basic', 'hmac')",
            name=op.f("ck_tool_auth_method_check"),
        ),
        sa.CheckConstraint(
            "risk_tier IN ('safe', 'caution', 'restricted')",
            name=op.f("ck_tool_risk_tier_check"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_tool_tenant_id_tenant"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tool")),
    )
    # db-schema §3.4 unique partial index
    op.execute(
        "CREATE UNIQUE INDEX idx_tool_tenant_slug ON tool "
        "(COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid), slug)"
    )
    op.execute("CREATE INDEX idx_tool_type ON tool (tool_type, enabled)")

    # ── 5. tool_invocation ────────────────────────────
    op.create_table(
        "tool_invocation",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column(
            "conversation_id",
            sa.UUID(),
            nullable=True,
            comment="logical FK conversation(id)",
        ),
        sa.Column(
            "message_id",
            sa.UUID(),
            nullable=True,
            comment="logical FK message — composite PK, no DB FK",
        ),
        sa.Column("tool_id", sa.UUID(), nullable=False),
        sa.Column("employee_id", sa.UUID(), nullable=True),
        sa.Column("skill_version_id", sa.UUID(), nullable=True),
        sa.Column(
            "input",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "output",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("cost_token", sa.Integer(), nullable=True),
        sa.Column(
            "policy_decision",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('success', 'error', 'timeout', 'rejected_by_policy')",
            name=op.f("ck_tool_invocation_status_check"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_tool_invocation_tenant_id_tenant"),
        ),
        sa.ForeignKeyConstraint(
            ["tool_id"],
            ["tool.id"],
            name=op.f("fk_tool_invocation_tool_id_tool"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tool_invocation")),
    )
    op.execute(
        "CREATE INDEX idx_tool_invocation_tenant_time "
        "ON tool_invocation (tenant_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX idx_tool_invocation_tool "
        "ON tool_invocation (tool_id, created_at DESC)"
    )
    op.create_index(
        "idx_tool_invocation_conv",
        "tool_invocation",
        ["conversation_id"],
    )

    # ── 6. tool_policy ────────────────────────────────
    op.create_table(
        "tool_policy",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.UUID(),
            nullable=True,
            comment="NULL = global rule",
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rule_yaml", sa.Text(), nullable=False),
        sa.Column(
            "priority",
            sa.Integer(),
            server_default="0",
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_tool_policy_tenant_id_tenant"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tool_policy")),
    )

    # ── 7. RLS ─────────────────────────────────────────
    # skill / tool / tool_policy 的 tenant_id 可為 NULL（系統/平台級）；
    # policy 接受「NULL 或 tenant 匹配」
    for tbl, with_null in [
        ("skill", True),
        ("skill_version", True),
        ("skill_binding", False),
        ("tool", True),
        ("tool_invocation", False),
        ("tool_policy", True),
    ]:
        op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY")
        if with_null:
            op.execute(
                f"CREATE POLICY {tbl}_tenant_isolation ON {tbl} USING ("
                "tenant_id IS NULL OR "
                "tenant_id::text = current_setting('app.tenant_id', true))"
            )
        else:
            op.execute(
                f"CREATE POLICY {tbl}_tenant_isolation ON {tbl} USING ("
                "tenant_id::text = current_setting('app.tenant_id', true))"
            )


def downgrade() -> None:
    for tbl in (
        "tool_policy",
        "tool_invocation",
        "tool",
        "skill_binding",
        "skill_version",
        "skill",
    ):
        op.execute(f"DROP POLICY IF EXISTS {tbl}_tenant_isolation ON {tbl}")

    op.drop_table("tool_policy")

    op.execute("DROP INDEX IF EXISTS idx_tool_invocation_tool")
    op.execute("DROP INDEX IF EXISTS idx_tool_invocation_tenant_time")
    op.drop_index("idx_tool_invocation_conv", table_name="tool_invocation")
    op.drop_table("tool_invocation")

    op.execute("DROP INDEX IF EXISTS idx_tool_type")
    op.execute("DROP INDEX IF EXISTS idx_tool_tenant_slug")
    op.drop_table("tool")

    op.drop_index("idx_skill_binding_emp_sv", table_name="skill_binding")
    op.drop_table("skill_binding")

    op.drop_index("idx_skill_version_tenant_status", table_name="skill_version")
    op.drop_index("idx_skill_version_skill_version", table_name="skill_version")
    op.drop_table("skill_version")

    op.execute("DROP INDEX IF EXISTS idx_skill_tenant_slug")
    op.drop_table("skill")
