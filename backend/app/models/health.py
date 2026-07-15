"""
Pydantic response models for health endpoints.

Pydantic v2 models serve two purposes:
  1. Runtime validation — ensures the data is correct
  2. OpenAPI schema generation — FastAPI auto-generates docs from these

Every field has a type annotation and a description.
The `model_config` with `json_schema_extra` provides example values
that appear in the interactive /docs page.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    """Status of a single downstream service (DB, cache, etc.)."""

    status: Literal["ok", "degraded", "down"] = Field(
        description="Current status of this service"
    )
    message: str = Field(
        default="",
        description="Human-readable status message",
    )
    latency_ms: float | None = Field(
        default=None,
        description="Round-trip latency to this service in milliseconds",
    )


class HealthResponse(BaseModel):
    """
    Response schema for GET /api/v1/health (liveness probe).

    Used by Kubernetes/Docker to know if the container is alive.
    """

    status: Literal["ok"] = Field(description="Always 'ok' if the process is alive")
    app_name: str = Field(description="Name of this application")
    version: str = Field(description="Semantic version of the running build")
    environment: str = Field(description="Deployment environment (dev/staging/prod)")
    timestamp: datetime = Field(description="UTC timestamp of this response")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ok",
                "app_name": "Adaptive AI Interview Assistant",
                "version": "0.1.0",
                "environment": "development",
                "timestamp": "2025-01-01T00:00:00Z",
            }
        }
    }


class ReadinessResponse(BaseModel):
    """
    Response schema for GET /api/v1/health/ready (readiness probe).

    Returns the health status of every downstream dependency.
    The outer `ready` field is the aggregate: True only if ALL services are ok.
    """

    ready: bool = Field(description="True only if ALL services are healthy")
    services: dict[str, ServiceStatus] = Field(
        description="Per-service health breakdown"
    )
    timestamp: datetime = Field(description="UTC timestamp of this response")

    model_config = {
        "json_schema_extra": {
            "example": {
                "ready": True,
                "services": {
                    "api": {"status": "ok", "message": "FastAPI is running"},
                },
                "timestamp": "2025-01-01T00:00:00Z",
            }
        }
    }
