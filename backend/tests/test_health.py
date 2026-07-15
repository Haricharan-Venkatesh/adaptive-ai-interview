"""
Pytest test suite for Phase 1, Milestone 1.1.

We use FastAPI's TestClient which runs the app in synchronous mode —
no actual server needs to be running.

Run with:   pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client() -> TestClient:
    """
    Create a test client for the FastAPI app.

    scope="module" means ONE client is created per test file — efficient.
    """
    return TestClient(app)


# ── Health endpoint tests ─────────────────────────────────────────────────────

class TestHealthEndpoint:
    """Tests for GET /api/v1/health (liveness probe)."""

    def test_health_returns_200(self, client: TestClient) -> None:
        """The endpoint must return HTTP 200."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self, client: TestClient) -> None:
        """The `status` field must be 'ok'."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "ok"

    def test_health_returns_app_name(self, client: TestClient) -> None:
        """Response must include the app name."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert "app_name" in data
        assert len(data["app_name"]) > 0

    def test_health_returns_version(self, client: TestClient) -> None:
        """Response must include a semantic version string."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert "version" in data
        # Simple version format check: X.Y.Z
        parts = data["version"].split(".")
        assert len(parts) == 3

    def test_health_returns_timestamp(self, client: TestClient) -> None:
        """Response must include a UTC timestamp."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert "timestamp" in data

    def test_health_has_process_time_header(self, client: TestClient) -> None:
        """Every response must include the X-Process-Time header."""
        response = client.get("/api/v1/health")
        assert "x-process-time" in response.headers

    def test_health_has_request_id_header(self, client: TestClient) -> None:
        """Every response must include the X-Request-ID header."""
        response = client.get("/api/v1/health")
        assert "x-request-id" in response.headers


class TestReadinessEndpoint:
    """Tests for GET /api/v1/health/ready (readiness probe)."""

    def test_readiness_returns_200(self, client: TestClient) -> None:
        """The endpoint must return HTTP 200."""
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200

    def test_readiness_returns_ready_true(self, client: TestClient) -> None:
        """In milestone 1.1 all services are ok so ready must be True."""
        response = client.get("/api/v1/health/ready")
        data = response.json()
        assert data["ready"] is True

    def test_readiness_includes_api_service(self, client: TestClient) -> None:
        """Services dict must include 'api' key."""
        response = client.get("/api/v1/health/ready")
        data = response.json()
        assert "api" in data["services"]
        assert data["services"]["api"]["status"] == "ok"


class TestRootEndpoint:
    """Tests for GET / (root redirect hint)."""

    def test_root_returns_200(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.status_code == 200

    def test_root_contains_docs_link(self, client: TestClient) -> None:
        data = client.get("/").json()
        assert "docs" in data


class TestOpenAPI:
    """Tests for OpenAPI schema generation."""

    def test_openapi_schema_available(self, client: TestClient) -> None:
        """The OpenAPI JSON schema must be accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_swagger_docs_available(self, client: TestClient) -> None:
        """Swagger UI must be accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
