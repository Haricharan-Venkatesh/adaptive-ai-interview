"""
Structured logging setup using structlog.

structlog produces JSON logs in production (machine-readable)
and pretty colored logs in development (human-readable).

Usage in ANY module:
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("something happened", user_id=123, action="login")
"""

import logging
import sys

import structlog

from app.core.config import settings


def setup_logging() -> None:
    """
    Configure structlog and stdlib logging.

    Call this ONCE at application startup before the server starts.
    FastAPI's lifespan function is the right place for this.
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # ── Shared processors (run for every log event) ───────────────────────
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,         # request-scoped data
        structlog.stdlib.add_logger_name,                # module name
        structlog.stdlib.add_log_level,                  # DEBUG / INFO / etc.
        structlog.stdlib.PositionalArgumentsFormatter(), # {}-style formatting
        structlog.processors.TimeStamper(fmt="iso"),     # ISO 8601 timestamp
        structlog.processors.StackInfoRenderer(),        # stack info if present
    ]

    # ── Choose renderer ───────────────────────────────────────────────────
    if settings.is_production:
        # JSON for log aggregation tools (DataDog, CloudWatch, Loki, etc.)
        renderer = structlog.processors.JSONRenderer()
    else:
        # Colored pretty output for local development
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Quiet down noisy third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a named structured logger.

    Args:
        name: Usually __name__ of the calling module.

    Returns:
        A structlog BoundLogger with key-value logging support.
    """
    return structlog.get_logger(name)  # type: ignore[return-value]
