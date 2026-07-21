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

from pydantic import Field, computed_field, model_validator
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
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=1, gt=0)
    reload: bool = Field(default=False)

    # ── CORS ─────────────────────────────────────────────────────────────────
    allowed_origins: str = Field(default="http://localhost:3000")

    # ── Logging ──────────────────────────────────────────────────────────────
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )

    # ── Redis ──────────────────────────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/0")
    session_ttl_seconds: int = Field(default=3600, gt=0)  # 1 hour

    # ── Database ───────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/interview_db"
    )

    # ── Graph Database (Neo4j) ──────────────────────────────────────────────
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="password")

    # ── AI / LLM ───────────────────────────────────────────────────────────
    gemini_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")

    # ── Vector Embeddings & RAG ────────────────────────────────────────────
    embedding_model_name: str = Field(default="all-MiniLM-L6-v2")
    chroma_persist_path: str = Field(default="./chroma_db")


    # ── Authentication & OAuth ───────────────────────────────────────────────
    jwt_secret_key: str = Field(default="changeme_jwt_secret")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=1440, gt=0)  # 24 hours
    # Model Config
    KNOWLEDGE_TRACER_MODEL: str = "bkt"  # "bkt" | "dkt" | "dkt_gnn"
    
    # Auth
    github_client_id: str = Field(default="", alias="GITHUB_CLIENT_ID")
    GITHUB_CLIENT_ID: str = Field(default="")
    github_client_secret: str = Field(default="")
    frontend_url: str = Field(default="http://localhost:3000")

    # ── Computed helpers ─────────────────────────────────────────────────────
    @computed_field  # type: ignore[misc]
    @property
    def cors_origins(self) -> list[str]:
        """Split comma-separated ALLOWED_ORIGINS into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @computed_field  # type: ignore[misc]
    @property
    def is_production(self) -> bool:
        """Returns True if the application is running in production mode."""
        return self.app_env == "production"

    @computed_field  # type: ignore[misc]
    @property
    def is_development(self) -> bool:
        """Returns True if the application is running in development mode."""
        return self.app_env == "development"

    # ── Validation ───────────────────────────────────────────────────────────
    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Enforce strict secret management when running in production."""
        if self.app_env == "production":
            if self.secret_key == "changeme":
                raise ValueError("secret_key must be configured in production")
            if self.jwt_secret_key == "changeme_jwt_secret":
                raise ValueError("jwt_secret_key must be configured in production")
            if not self.gemini_api_key:
                raise ValueError("gemini_api_key must be set in production")
            
            # Enforce GitHub OAuth secret if client ID is configured
            if self.github_client_id and not self.github_client_secret:
                raise ValueError("github_client_secret must be set if github_client_id is provided")
        return self


# ── Cached singleton ─────────────────────────────────────────────────────────
# lru_cache ensures the Settings object is created ONCE and reused everywhere.
# This avoids reading .env hundreds of times during a request.
@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings singleton."""
    return Settings()


# Module-level alias for convenience:   from app.core.config import settings
settings = get_settings()
