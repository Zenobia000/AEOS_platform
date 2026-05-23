"""WebhookEvent — webhook idempotency / dedup 表.

依 db-schema.md §4.8 + MC-011 + API-002 LINE webhook:
- 複合 PK (id, channel) — channel-specific event id 才唯一
- 進入 webhook 時 INSERT 一筆；如違反 PK 即 dedup 命中（不重複處理）
- 7 天後可清除（idx_webhook_event_purge 用於 cron purge）
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Index, PrimaryKeyConstraint, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base


class WebhookEvent(Base):
    __tablename__ = "webhook_event"

    id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="e.g. LINE webhookEventId",
    )
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        PrimaryKeyConstraint("id", "channel", name="pk_webhook_event"),
        Index("idx_webhook_event_purge", "received_at"),
    )
