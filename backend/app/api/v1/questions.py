"""
Question API router.

Endpoints:
  POST   /api/v1/questions         — Create a new question
  GET    /api/v1/questions         — List questions (paginated)
  GET    /api/v1/questions/search  — Search/filter questions
  GET    /api/v1/questions/{id}    — Retrieve a single question
  PATCH  /api/v1/questions/{id}    — Update a question
  DELETE /api/v1/questions/{id}    — Delete a question
"""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.postgres import get_db_session
from app.models.question import QuestionCreate, QuestionResponse, QuestionUpdate
from app.services import question_engine

logger = get_logger(__name__)

router = APIRouter(prefix="/questions", tags=["Questions"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.post(
    "",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new question",
)
async def create_question(
    request: QuestionCreate, session: DbSession
) -> QuestionResponse:
    return await question_engine.create_question(session, request)


@router.get(
    "/search",
    response_model=list[QuestionResponse],
    summary="Search questions",
)
async def search_questions(
    session: DbSession,
    topic: str | None = Query(None, description="Exact topic name"),
    difficulty_min: int | None = Query(None, ge=1, le=10),
    difficulty_max: int | None = Query(None, ge=1, le=10),
    limit: int = Query(10, ge=1, le=100),
    randomize: bool = Query(True, description="Order by random for adaptive engine"),
    exclude_ids: list[str] | None = Query(None, description="Question IDs to exclude (already asked)"),  # noqa: B008
) -> Sequence[QuestionResponse]:
    return await question_engine.search_questions(
        session, topic, difficulty_min, difficulty_max, limit, randomize, exclude_ids
    )


@router.get(
    "",
    response_model=list[QuestionResponse],
    summary="List all questions",
)
async def list_questions(
    session: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> Sequence[QuestionResponse]:
    return await question_engine.list_questions(session, skip, limit)


@router.get(
    "/{question_id}",
    response_model=QuestionResponse,
    summary="Get question by ID",
)
async def get_question(question_id: str, session: DbSession) -> QuestionResponse:
    question = await question_engine.get_question(session, question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question '{question_id}' not found.",
        )
    return question


@router.patch(
    "/{question_id}",
    response_model=QuestionResponse,
    summary="Update a question",
)
async def update_question(
    question_id: str, update_data: QuestionUpdate, session: DbSession
) -> QuestionResponse:
    question = await question_engine.update_question(session, question_id, update_data)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question '{question_id}' not found.",
        )
    return question


@router.delete(
    "/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a question",
)
async def delete_question(question_id: str, session: DbSession) -> None:
    deleted = await question_engine.delete_question(session, question_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question '{question_id}' not found.",
        )
