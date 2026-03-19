from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_ENV: str = "dev"
    APP_NAME: str = "local-delivery"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "DEBUG"

    # PostgreSQL — write primary
    DATABASE_URL: str = (
        "postgresql+asyncpg://delivery_user:delivery_pass@postgres:5432/local_delivery"
    )
    # PostgreSQL — read replica (same as write in dev)
    READ_DATABASE_URL: str = (
        "postgresql+asyncpg://delivery_user:delivery_pass@postgres:5432/local_delivery"
    )

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_AVAILABILITY_TTL: int = 60

    # Security
    JWT_SECRET_KEY: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"

    # CORS — stored as a list; populated from comma-separated env var
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
