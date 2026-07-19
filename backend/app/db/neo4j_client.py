import logging
from datetime import UTC, datetime

from neo4j import AsyncGraphDatabase, AsyncDriver

from app.core.config import settings
from app.models.health import ServiceStatus

logger = logging.getLogger(__name__)

# Global driver instance
_driver: AsyncDriver | None = None

async def init_neo4j() -> None:
    """Initialize the global Neo4j driver."""
    global _driver
    if _driver is not None:
        logger.warning("Neo4j driver is already initialized")
        return

    logger.info("Initializing Neo4j driver at %s", settings.neo4j_uri)
    try:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
        # Verify connection
        await _driver.verify_connectivity()
        logger.info("Neo4j driver successfully connected.")
    except Exception as e:
        logger.error("Failed to connect to Neo4j: %s", e)
        _driver = None
        raise

async def close_neo4j() -> None:
    """Close the Neo4j driver gracefully."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver closed.")

def is_neo4j_initialized() -> bool:
    """Check if the global driver is initialized."""
    return _driver is not None

async def check_neo4j_health() -> ServiceStatus:
    """
    Health check for Neo4j.
    Used by the readiness probe.
    """
    if _driver is None:
        return ServiceStatus(
            status="down",
            message="Neo4j driver is not initialized",
            timestamp=datetime.now(UTC),
        )

    try:
        # Run a simple query to ensure the database is responding
        async with _driver.session() as session:
            result = await session.run("RETURN 1 AS n")
            record = await result.single()
            if record and record["n"] == 1:
                return ServiceStatus(
                    status="ok",
                    message="Neo4j is responding",
                    timestamp=datetime.now(UTC),
                )
            else:
                return ServiceStatus(
                    status="down",
                    message="Neo4j returned unexpected response",
                    timestamp=datetime.now(UTC),
                )
    except Exception as e:
        logger.error("Neo4j health check failed: %s", e)
        return ServiceStatus(
            status="down",
            message=str(e),
            timestamp=datetime.now(UTC),
        )

async def execute_query(query: str, parameters: dict | None = None) -> list[dict]:
    """
    Helper function to execute a Cypher query.
    Returns a list of dictionaries.
    """
    if _driver is None:
        raise RuntimeError("Neo4j driver is not initialized")
    
    async with _driver.session() as session:
        result = await session.run(query, parameters or {})
        records = await result.data()
        return records
