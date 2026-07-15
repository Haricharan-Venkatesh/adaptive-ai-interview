"""
Redis connection pool manager.

Design:
  - Module-level singleton pool created ONCE at startup via init_redis_pool()
  - get_redis() is a FastAPI async-generator dependency — injected into route handlers
  - check_redis_health() is called by the readiness probe
  - is_redis_initialized() lets the readiness probe skip the Redis check in test mode
    (when no pool was created), keeping existing health tests backward-compatible

ADR-002: Redis chosen for sub-ms latency, native TTL, and pub/sub capabilities.
"""

import time
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, ResponseError, TimeoutError

from app.core.config import settings
from app.core.logging import get_logger
from app.models.health import ServiceStatus

logger = get_logger(__name__)

# ── Module-level singleton ────────────────────────────────────────────────────
# Created once at lifespan startup; never re-created per request.
_pool: Redis | None = None


async def init_redis_pool() -> None:
    """
    Create the async Redis connection pool.

    Called exactly once from main.py lifespan startup.
    Does NOT raise on failure — the readiness probe surfaces the error instead.
    This allows the app to start even when Redis is temporarily unavailable.
    """
    global _pool
    try:
        _pool = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,        # all keys/values are str, not bytes
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,     # background keepalive ping
        )
        await _pool.ping()
        logger.info(
            "Redis pool initialized",
            url=settings.redis_url,
            ttl_seconds=settings.session_ttl_seconds,
        )
    except Exception as exc:
        # Graceful degradation: app starts, readiness probe shows Redis as "down"
        logger.warning(
            "Redis unavailable at startup — sessions will fail until Redis is ready",
            url=settings.redis_url,
            error=str(exc),
        )
        _pool = None


async def close_redis_pool() -> None:
    """Close the connection pool on application shutdown."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None
        logger.info("Redis pool closed")


def is_redis_initialized() -> bool:
    """Return True if the Redis pool has been successfully created."""
    return _pool is not None


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    FastAPI dependency — yields the Redis client for the duration of a request.

    Usage in a route:
        async def my_route(redis: Redis = Depends(get_redis)):
            ...

    Raises RuntimeError if the pool was never initialized (app startup failure).
    In tests, this dependency is overridden with a fakeredis client.
    """
    if _pool is None:
        raise RuntimeError(
            "Redis pool is not initialized. "
            "Check that Redis is running and REDIS_URL is correct."
        )
    yield _pool


async def check_redis_health() -> ServiceStatus:
    """
    Ping Redis and return a ServiceStatus for the readiness probe.

    Only called when is_redis_initialized() is True.
    """
    if _pool is None:
        return ServiceStatus(status="down", message="Redis pool not initialized")
    try:
        start = time.perf_counter()
        await _pool.ping()
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return ServiceStatus(
            status="ok",
            message="Redis is reachable",
            latency_ms=latency_ms,
        )
    except (ConnectionError, TimeoutError, ResponseError, Exception) as exc:
        return ServiceStatus(
            status="down",
            message=f"Redis ping failed: {exc}",
        )
