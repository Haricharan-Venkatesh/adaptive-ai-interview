"""
FastAPI application factory and entry point.

Architecture decision:
  We use the "application factory" pattern — create_app() returns the app.
  This makes it easy to create separate app instances for testing.

Lifespan:
  FastAPI's `lifespan` context manager replaces the deprecated
  @app.on_event("startup") and @app.on_event("shutdown") decorators.
  Everything inside `async with lifespan(app):` runs around the server.
"""

import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.db.redis_client import close_redis_pool, init_redis_pool

logger = get_logger(__name__)


# ── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Code BEFORE `yield` runs at startup.
    Code AFTER `yield` runs at shutdown.

    Future milestones will:
      - Initialize PostgreSQL connection pool
      - Connect to Redis
      - Connect to Neo4j
      - Load ML models into memory
    """
    # ── Startup ────────────────────────────────────────────────────────────
    setup_logging()
    logger.info(
        "Starting application",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        debug=settings.debug,
    )
    await init_redis_pool()   # M1.2 — graceful: logs warning if Redis unavailable

    yield  # Server is running and serving requests

    # ── Shutdown ────────────────────────────────────────────────────────────
    await close_redis_pool()  # M1.2 — clean shutdown
    logger.info("Shutting down application", app_name=settings.app_name)


# ── Application Factory ───────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns a fully configured app instance ready to be served by uvicorn.
    """
    app = FastAPI(
        title=settings.app_name,
        description=(
            "Production-ready Adaptive AI Interview Assistant. "
            "Asks adaptive questions, analyzes answers, "
            "models candidate knowledge, and generates interview reports."
        ),
        version=settings.app_version,
        docs_url="/docs",           # Swagger UI (disable in production if needed)
        redoc_url="/redoc",         # ReDoc UI
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────
    _register_middleware(app)

    # ── Routers ───────────────────────────────────────────────────────────
    app.include_router(api_router)

    # ── Root endpoint ─────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        """Redirect hint for the API root."""
        return {
            "message": f"Welcome to {settings.app_name}",
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    logger.info("Application created successfully")
    return app


def _register_middleware(app: FastAPI) -> None:
    """Register all middleware in correct order (outermost = last registered)."""

    # ── CORS ─────────────────────────────────────────────────────────────
    # Must be first so preflight OPTIONS requests are handled correctly.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── GZip compression ─────────────────────────────────────────────────
    # Compresses responses larger than 1 KB automatically.
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # ── Request timing middleware ─────────────────────────────────────────
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next) -> Response:
        """
        Adds X-Process-Time header to every response.

        This is industry standard — helps with debugging slow endpoints.
        You can see it in your browser's Network tab or curl output.
        """
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
        return response

    # ── Request ID middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def add_request_id(request: Request, call_next) -> Response:
        """
        Adds a unique X-Request-ID to every request for tracing.

        In production you'd use a proper distributed tracing system (e.g.,
        OpenTelemetry). This is the simple version for now.
        """
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# ── App instance ──────────────────────────────────────────────────────────────
# This is what uvicorn imports: `uvicorn app.main:app`
app = create_app()
