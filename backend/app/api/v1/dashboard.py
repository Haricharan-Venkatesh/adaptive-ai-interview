import logging
from typing import Any

from fastapi import APIRouter, Query, status

from app.models.dashboard import CodeMapGraphResponse
from app.services import dashboard_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/codemap",
    response_model=CodeMapGraphResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Candidate Code Map Graph",
    description="Retrieve candidate concept graph (nodes and relationships) from Neo4j DB for output dashboard visualization."
)
async def get_candidate_codemap(
    session_id: str | None = Query(None, description="Optional interview session identifier")
) -> Any:
    """API endpoint to fetch Neo4j graph data for Phase 5 Output Dashboard."""
    logger.info("Received request for candidate codemap graph (session_id=%s)", session_id)
    response = await dashboard_service.fetch_codemap_graph(session_id=session_id)
    return response
