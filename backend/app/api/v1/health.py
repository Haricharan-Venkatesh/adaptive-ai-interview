"""
Health check API router.

Endpoints:
  GET /api/v1/health          — liveness probe  (is the process alive?)
  GET /api/v1/health/ready    — readiness probe (are all dependencies ready?)

These two endpoints are standard Kubernetes/Docker health check targets.
Even without K8s, they are useful for monitoring services.
"""

from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import settings
from app.core.logging import get_logger
from app.models.health import HealthResponse, ReadinessResponse, ServiceStatus

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Liveness probe",
    description=(
        "Returns 200 if the process is running. "
        "Use this to check whether the application is alive."
    ),
)
async def health_check() -> HealthResponse:
    """
    Liveness probe.

    Kubernetes (and Docker health-check) hits this every few seconds.
    It should ONLY check if the process itself is responsive — not databases.
    """
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
        "Returns 200 if the app AND all dependencies are ready to serve traffic. "
        "Returns 503 if any dependency is unhealthy."
    ),
)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness probe.

    In future milestones this will check:
      - PostgreSQL connection
      - Redis connection
      - Neo4j connection

    For now it always returns healthy because we have no dependencies yet.
    """
    logger.debug("Readiness check requested")

    services: dict[str, ServiceStatus] = {
        "api": ServiceStatus(status="ok", message="FastAPI is running"),
        # Future milestones will add:
        # "postgres": await check_postgres(),
        # "redis":    await check_redis(),
        # "neo4j":    await check_neo4j(),
    }

    all_healthy = all(s.status == "ok" for s in services.values())

    return ReadinessResponse(
        ready=all_healthy,
        services=services,
        timestamp=datetime.now(UTC),
    )
