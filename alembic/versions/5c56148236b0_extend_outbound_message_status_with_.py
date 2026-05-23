"""extend outbound_message status with awaiting_review + rejected (Draft Mode)

Revision ID: 5c56148236b0
Revises: 71c271e944a4
Create Date: 2026-05-22

對應 PRD-001 §5.4 Draft Mode (F-DFT-01/02/03):
- AI 產 draft 後不直接 push；先 status='awaiting_review' 等 expert 審
- expert approve → status='pending'（讓 OutboundProcessor 撿）
- expert reject → status='rejected'（不 push；通常配合建 conversation_handoff）
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5c56148236b0"
down_revision: str | Sequence[str] | None = "71c271e944a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE outbound_message DROP CONSTRAINT IF EXISTS ck_outbound_message_status_check"
    )
    op.execute(
        "ALTER TABLE outbound_message ADD CONSTRAINT ck_outbound_message_status_check "
        "CHECK (status IN ('pending', 'sent', 'failed', 'retrying', "
        "'awaiting_review', 'rejected'))"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE outbound_message DROP CONSTRAINT IF EXISTS ck_outbound_message_status_check"
    )
    op.execute(
        "ALTER TABLE outbound_message ADD CONSTRAINT ck_outbound_message_status_check "
        "CHECK (status IN ('pending', 'sent', 'failed', 'retrying'))"
    )
