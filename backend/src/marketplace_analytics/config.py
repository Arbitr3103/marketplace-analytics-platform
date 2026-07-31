"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. Real provider credentials are intentionally out of scope."""

    model_config = SettingsConfigDict(
        env_prefix="MAP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["local", "test", "production"] = "local"
    demo_mode: bool = True
    database_url: str = "postgresql+asyncpg://analytics:analytics@localhost:5432/analytics"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = Field(default=300, ge=1, le=86_400)
    cors_allowed_origins: tuple[str, ...] = ("http://localhost:3000",)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
