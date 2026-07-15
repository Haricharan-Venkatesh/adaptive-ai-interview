"""
Session service — business logic for interview session management.

All functions are pure async and accept a Redis client as their first argument.
This design (dependency injection via FastAPI Depends) makes them trivially testable:
swap the real Redis for a fakeredis instance in tests without mocking internals.

Redis key schema:
  session:{session_id}  →  JSON-serialized InterviewSession
  TTL is set on every write and preserved (TTL = remaining time) on update.

Operations:
  create_session          POST /sessions
  get_session             GET  /sessions/{id}
  update_session          PATCH /sessions/{id}
  delete_session          DELETE /sessions/{id}
  append_question_record  POST /sessions/{id}/questions
"""

from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import get_logger
from app.models.session import (
    AppendQuestionRequest,
    CreateSessionRequest,
    InterviewSession,
    QuestionRecord,
    UpdateSessionRequest,
)

logger = get_logger(__name__)

_KEY_PREFIX = "session:"


def _key(session_id: str) -> str:
    """Build the Redis key for a session."""
    return f"{_KEY_PREFIX}{session_id}"


async def create_session(
    redis: Redis,
    request: CreateSessionRequest,
) -> InterviewSession:
    """
    Create a new interview session and persist it in Redis with TTL.

    Returns the fully initialized InterviewSession.
    """
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.session_ttl_seconds)
    session = InterviewSession(
        candidate_id=request.candidate_id,
        topic=request.topic,
        difficulty_level=request.difficulty_level,
        expires_at=expires_at,
        metadata=request.metadata,
    )
    await redis.set(
        _key(session.session_id),
        session.model_dump_json(),
        ex=settings.session_ttl_seconds,
    )
    logger.info(
        "Interview session created",
        session_id=session.session_id,
        candidate_id=request.candidate_id,
        topic=request.topic.value,
        difficulty=request.difficulty_level,
        ttl_seconds=settings.session_ttl_seconds,
    )
    return session


async def get_session(redis: Redis, session_id: str) -> InterviewSession | None:
    """
    Retrieve a session by ID.

    Returns None if the session does not exist or has expired.
    Redis automatically deletes expired keys, so a missing key = expired session.
    """
    raw = await redis.get(_key(session_id))
    if raw is None:
        return None
    return InterviewSession.model_validate_json(raw)


async def update_session(
    redis: Redis,
    session_id: str,
    update: UpdateSessionRequest,
) -> InterviewSession | None:
    """
    Partially update a session (HTTP PATCH semantics).

    Preserves the remaining TTL — updating a session does not reset its expiry.
    Returns None if the session does not exist.
    """
    session = await get_session(redis, session_id)
    if session is None:
        return None

    # Only apply fields that were explicitly provided (not None)
    update_data = update.model_dump(exclude_none=True)
    updated = session.model_copy(update=update_data)

    # Preserve remaining TTL rather than resetting it
    remaining_ttl = await redis.ttl(_key(session_id))
    ttl = remaining_ttl if remaining_ttl > 0 else settings.session_ttl_seconds

    await redis.set(_key(session_id), updated.model_dump_json(), ex=ttl)
    logger.info(
        "Session updated",
        session_id=session_id,
        updated_fields=list(update_data.keys()),
        remaining_ttl_seconds=ttl,
    )
    return updated


async def delete_session(redis: Redis, session_id: str) -> bool:
    """
    Delete a session explicitly.

    Returns True if the session existed and was deleted.
    Returns False if the session was not found (already expired or never created).
    """
    count = await redis.delete(_key(session_id))
    deleted = count > 0
    if deleted:
        logger.info("Session deleted", session_id=session_id)
    else:
        logger.debug("Delete attempted on non-existent session", session_id=session_id)
    return deleted


async def append_question_record(
    redis: Redis,
    session_id: str,
    request: AppendQuestionRequest,
) -> InterviewSession | None:
    """
    Append a QuestionRecord to session.question_history.

    Also increments total_questions_asked and updates current_question_index.
    Preserves TTL on write.
    Returns None if the session does not exist.
    """
    session = await get_session(redis, session_id)
    if session is None:
        return None

    record = QuestionRecord(
        question_text=request.question_text,
        topic=request.topic,
        difficulty=request.difficulty,
        answer_text=request.answer_text,
        score=request.score,
        feedback=request.feedback,
    )

    session.question_history.append(record)
    session.total_questions_asked += 1
    session.current_question_index = len(session.question_history) - 1

    remaining_ttl = await redis.ttl(_key(session_id))
    ttl = remaining_ttl if remaining_ttl > 0 else settings.session_ttl_seconds

    await redis.set(_key(session_id), session.model_dump_json(), ex=ttl)
    logger.info(
        "Question record appended",
        session_id=session_id,
        question_id=record.question_id,
        total_questions=session.total_questions_asked,
        topic=request.topic,
        difficulty=request.difficulty,
    )
    return session
