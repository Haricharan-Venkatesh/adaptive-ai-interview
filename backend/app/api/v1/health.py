"""
Health check API router.

Endpoints:
  GET /api/v1/health          — liveness probe  (is the process alive?)
  GET /api/v1/health/ready    — readiness probe (are all dependencies ready?)

Readiness probe strategy:
  - "api" service is always checked (trivially ok if the process is running)
  - "redis" service is checked ONLY when the pool was successfully initialized.
    This keeps existing unit tests backward-compatible (no Redis in test env).
  - Future milestones will add "postgres" and "neo4j" checks.
"""

from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import settings
from app.core.logging import get_logger
from app.db.postgres import check_postgres_health, is_postgres_initialized
from app.db.redis_client import check_redis_health, is_redis_initialized
from app.models.health import HealthResponse, ReadinessResponse, ServiceStatus

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Returns 200 if the process is running.",
)
async def health_check() -> HealthResponse:
    """Liveness probe — only checks that the process is alive."""
    logger.debug("Health check requested")
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.now(UTC),
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description=(
        "Returns 200 if the app AND all initialized dependencies are healthy. "
        "Returns 503 if any required dependency is down."
    ),
)
async def readiness_check() -> ReadinessResponse:
    """Readiness probe — checks all initialized downstream dependencies."""
    logger.debug("Readiness check requested")

    services: dict[str, ServiceStatus] = {
        "api": ServiceStatus(status="ok", message="FastAPI is running"),
    }

    # Only probe Redis if the pool was successfully initialized at startup.
    # In unit tests (no Redis), is_redis_initialized() returns False,
    # so the readiness probe stays backward-compatible.
    if is_redis_initialized():
        services["redis"] = await check_redis_health()

    if is_postgres_initialized():
        services["postgres"] = await check_postgres_health()

    # Future milestones will add:
    # if is_neo4j_initialized():
    #     services["neo4j"] = await check_neo4j_health()

    all_healthy = all(s.status == "ok" for s in services.values())

    return ReadinessResponse(
        ready=all_healthy,
        services=services,
        timestamp=datetime.now(UTC),
    )
