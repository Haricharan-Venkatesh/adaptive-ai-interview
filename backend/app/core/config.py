"""
Core configuration module.

Uses pydantic-settings to automatically read values from:
  1. The .env file
  2. Environment variables (which override .env)

This is the SINGLE SOURCE OF TRUTH for all configuration.
Every other module should import `settings` from here.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables / .env file.

    All fields have type annotations so Pydantic validates them at startup.
    If a required field is missing the app will refuse to start — this is
    intentional and prevents misconfigured deployments.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # ignore unknown keys in .env
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = Field(default="Adaptive AI Interview Assistant")
    app_version: str = Field(default="0.1.0")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development"
    )
    debug: bool = Field(default=False)
    secret_key: str = Field(default="changeme")

    # ── Server ───────────────────────────────────────────────────────────────
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=1)
    reload: bool = Field(default=False)

    # ── CORS ─────────────────────────────────────────────────────────────────
    allowed_origins: str = Field(default="http://localhost:3000")

    # ── Logging ──────────────────────────────────────────────────────────────
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )

    # ── Computed helpers ─────────────────────────────────────────────────────
    @computed_field  # type: ignore[misc]
    @property
    def cors_origins(self) -> list[str]:
        """Split comma-separated ALLOWED_ORIGINS into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @computed_field  # type: ignore[misc]
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @computed_field  # type: ignore[misc]
    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


# ── Cached singleton ─────────────────────────────────────────────────────────
# lru_cache ensures the Settings object is created ONCE and reused everywhere.
# This avoids reading .env hundreds of times during a request.
@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings singleton."""
    return Settings()


# Module-level alias for convenience:   from app.core.config import settings
settings = get_settings()
