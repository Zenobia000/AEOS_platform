"""Application settings loaded from environment variables.

依 ADR-0011 採 Pydantic Settings v2；S2 起隨模組逐步擴充欄位。
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="aeos-platform")
    app_env: str = Field(default="dev", description="dev / staging / prod")
    app_version: str = Field(default="0.0.1")

    database_url: str = Field(
        default="postgresql+asyncpg://aeos:aeos_dev_only@localhost:5432/aeos",
        description="Async PG DSN (asyncpg driver)",
    )
    database_url_sync: str = Field(
        default="postgresql+psycopg://aeos:aeos_dev_only@localhost:5432/aeos",
        description="Sync PG DSN for Alembic migrations",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
