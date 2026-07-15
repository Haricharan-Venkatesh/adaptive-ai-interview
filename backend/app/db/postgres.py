"""
PostgreSQL database connection and session management.

Design:
  - Uses SQLAlchemy 2.x async engine and sessionmaker.
  - `get_db_session()` is a FastAPI dependency yielding an AsyncSession.
  - Lifecycle events (`init_db`, `close_db`) manage the connection pool.
  - `check_postgres_health()` is called by the readiness probe.
"""

import time
from collections.abc import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.logging import get_logger
from app.models.health import ServiceStatus

logger = get_logger(__name__)

# Module-level singleton for the engine
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    """
    Initialize the async database engine and session factory.
    
    Called once at application startup.
    Does NOT raise on failure to allow the app to start (graceful degradation),
    so the readiness probe can surface the failure.
    """
    global _engine, _session_factory
    try:
        # pool_pre_ping ensures connections are alive before being used
        _engine = create_async_engine(
            settings.database_url,
            pool_pre_ping=True,
            echo=settings.is_development,  # Log SQL queries in dev mode
        )
        _session_factory = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        
        # Test connection
        async with _engine.begin() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
            
        logger.info("PostgreSQL connection pool initialized", url=settings.database_url)
    except Exception as exc:
        logger.warning(
            "PostgreSQL unavailable at startup — database endpoints will fail",
            url=settings.database_url,
            error=str(exc),
        )
        _engine = None
        _session_factory = None


async def close_db() -> None:
    """Close the database engine on application shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("PostgreSQL connection pool closed")


def is_postgres_initialized() -> bool:
    """Return True if the database engine has been successfully created."""
    return _engine is not None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding a SQLAlchemy AsyncSession.
    
    Raises RuntimeError if the engine was never initialized.
    """
    if _session_factory is None:
        raise RuntimeError(
            "Database pool is not initialized. "
            "Check that PostgreSQL is running and DATABASE_URL is correct."
        )
    
    async with _session_factory() as session:
        try:
            yield session
            # We don't auto-commit here, the service layer handles transaction boundaries.
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_postgres_health() -> ServiceStatus:
    """
    Ping PostgreSQL and return a ServiceStatus for the readiness probe.
    
    Only called when is_postgres_initialized() is True.
    """
    if _engine is None:
        return ServiceStatus(status="down", message="PostgreSQL pool not initialized")
    
    try:
        start = time.perf_counter()
        async with _engine.begin() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return ServiceStatus(
            status="ok",
            message="PostgreSQL is reachable",
            latency_ms=latency_ms,
        )
    except SQLAlchemyError as exc:
        return ServiceStatus(
            status="down",
            message=f"PostgreSQL ping failed: {exc}",
        )
