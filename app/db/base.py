"""SQLAlchemy declarative base + 統一命名慣例.

依 db-schema.md 慣例：
- 表名 snake_case 複數（tenants, api_keys, audit_logs）
- PK 為 `id` 或 `<entity>_id` BIGSERIAL
- timestamp 欄位：created_at / updated_at，TIMESTAMPTZ
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """All ORM models inherit this."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
