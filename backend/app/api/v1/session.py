"""
Session API router — interview session lifecycle endpoints.

Endpoints:
  POST   /api/v1/sessions                      — Create a new session
  GET    /api/v1/sessions/{session_id}          — Retrieve a session
  PATCH  /api/v1/sessions/{session_id}          — Partial update
  DELETE /api/v1/sessions/{session_id}          — Delete / end session
  POST   /api/v1/sessions/{session_id}/questions — Append Q&A record

All endpoints inject Redis via Annotated[Redis, Depends(get_redis)].
This satisfies ruff B008 (no function calls in argument defaults).
In tests, get_redis is overridden via app.dependency_overrides.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis

from app.core.logging import get_logger
from app.db.redis_client import get_redis
from app.models.session import (
    AppendQuestionRequest,
    CreateSessionRequest,
    InterviewSession,
    UpdateSessionRequest,
)
from app.services import session_service

logger = get_logger(__name__)

router = APIRouter(prefix="/sessions", tags=["Sessions"])

# Type alias — satisfies ruff B008 by moving Depends out of the function signature
RedisDep = Annotated[Redis, Depends(get_redis)]


@router.post(
    "",
    response_model=InterviewSession,
    status_code=status.HTTP_201_CREATED,
    summary="Create interview session",
    description=(
        "Creates a new interview session for a candidate. "
        "The session is stored in Redis with a configurable TTL (default 1 hour). "
        "Returns the full session object including the generated session_id."
    ),
)
async def create_session(
    request: CreateSessionRequest,
    redis: RedisDep,
) -> InterviewSession:
    """Create a new interview session."""
    return await session_service.create_session(redis, request)


@router.get(
    "/{session_id}",
    response_model=InterviewSession,
    summary="Get interview session",
    description="Retrieve an active interview session by its ID. Returns 404 if expired or not found.",
)
async def get_session(
    session_id: str,
    redis: RedisDep,
) -> InterviewSession:
    """Retrieve an interview session by ID."""
    session = await session_service.get_session(redis, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or has expired.",
        )
    return session


@router.patch(
    "/{session_id}",
    response_model=InterviewSession,
    summary="Update interview session",
    description=(
        "Partially update a session. Only provided fields are updated. "
        "The Redis TTL is preserved (not reset). Returns 404 if session not found."
    ),
)
async def update_session(
    session_id: str,
    update: UpdateSessionRequest,
    redis: RedisDep,
) -> InterviewSession:
    """Partially update an interview session."""
    session = await session_service.update_session(redis, session_id, update)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or has expired.",
        )
    return session


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete interview session",
    description="Delete a session explicitly. Returns 204 on success, 404 if not found.",
)
async def delete_session(
    session_id: str,
    redis: RedisDep,
) -> None:
    """Delete (end) an interview session."""
    deleted = await session_service.delete_session(redis, session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or has expired.",
        )


@router.post(
    "/{session_id}/questions",
    response_model=InterviewSession,
    summary="Append question record",
    description=(
        "Append a question-answer record to the session's question history. "
        "Called after each interview exchange. "
        "Increments total_questions_asked and updates current_question_index."
    ),
)
async def append_question(
    session_id: str,
    request: AppendQuestionRequest,
    redis: RedisDep,
) -> InterviewSession:
    """Append a Q&A record to the session's question history."""
    session = await session_service.append_question_record(redis, session_id, request)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or has expired.",
        )
    return session
