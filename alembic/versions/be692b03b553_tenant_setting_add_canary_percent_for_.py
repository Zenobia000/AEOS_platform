"""tenant_setting add canary_percent for auto-reply routing

Revision ID: be692b03b553
Revises: 155e92a056c7
Create Date: 2026-05-23

對應 S5 §Canary：per-tenant 漸進放鬆 Draft Mode → auto-reply。
- canary_percent (0-100)：多少 % outbound 直送（status='pending'）
  剩餘走 Draft Mode (status='awaiting_review')
- 預設 0 = 全 Draft Mode（保守，pilot 上線初值）
- 100 = 全 auto-reply（pass_rate ≥ 0.8 後可調）
- bucket 決定基於 conversation.id hash 取模 → 同 conversation 永遠同 bucket
  (避免同一 conversation 部分 draft 部分 auto，UX 一致)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "be692b03b553"
down_revision: str | Sequence[str] | None = "155e92a056c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tenant_setting",
        sa.Column(
            "canary_percent",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.create_check_constraint(
        "tenant_setting_canary_percent_check",
        "tenant_setting",
        "canary_percent >= 0 AND canary_percent <= 100",
    )


def downgrade() -> None:
    op.drop_constraint(
        "tenant_setting_canary_percent_check", "tenant_setting", type_="check"
    )
    op.drop_column("tenant_setting", "canary_percent")
