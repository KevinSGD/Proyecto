"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration — every field can be overridden via env vars."""

    app_name: str = "Scheduler API"
    app_version: str = "0.3.0"
    debug: bool = False
    log_level: str = "INFO"

    database_url: str = "sqlite:///scheduler.db"

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_allow_credentials: bool = True

    solver_max_time_seconds: int = 10
    solver_num_workers: int = 8

    api_prefix: str = "/api/v1"

    secret_key: str = "CHANGE-ME-IN-PRODUCTION-use-openssl-rand-hex-32"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    model_config = {"env_prefix": "SCHEDULER_", "env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
