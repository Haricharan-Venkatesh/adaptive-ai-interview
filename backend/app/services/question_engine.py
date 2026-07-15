"""
Question Engine — business logic for retrieving and filtering questions.

All functions are pure async and accept an AsyncSession as their first argument.
This makes testing trivial (can inject a mocked or test session).
"""

from collections.abc import Sequence

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.logging import get_logger
from app.models.question import Question, QuestionCreate, QuestionUpdate

logger = get_logger(__name__)


async def create_question(session: AsyncSession, question_data: QuestionCreate) -> Question:
    """Create a new question in the database."""
    new_q = Question(**question_data.model_dump())
    session.add(new_q)
    await session.commit()
    await session.refresh(new_q)
    logger.info("Question created", question_id=new_q.id, title=new_q.title)
    return new_q


async def get_question(session: AsyncSession, question_id: str) -> Question | None:
    """Retrieve a single question by ID."""
    stmt = select(Question).where(Question.id == question_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_question(
    session: AsyncSession, question_id: str, update_data: QuestionUpdate
) -> Question | None:
    """Partially update a question."""
    question = await get_question(session, question_id)
    if not question:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(question, key, value)
        
    await session.commit()
    await session.refresh(question)
    logger.info("Question updated", question_id=question.id, updated_fields=list(update_dict.keys()))
    return question


async def delete_question(session: AsyncSession, question_id: str) -> bool:
    """Delete a question by ID."""
    question = await get_question(session, question_id)
    if not question:
        return False
        
    await session.delete(question)
    await session.commit()
    logger.info("Question deleted", question_id=question_id)
    return True


async def list_questions(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> Sequence[Question]:
    """Retrieve a paginated list of questions."""
    stmt = select(Question).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def search_questions(
    session: AsyncSession, 
    topic: str | None = None, 
    difficulty_min: int | None = None, 
    difficulty_max: int | None = None,
    limit: int = 10,
    randomize: bool = False
) -> Sequence[Question]:
    """
    Search and filter questions. 
    Can be used by the adaptive engine to find next questions.
    """
    stmt = select(Question)
    
    if topic:
        stmt = stmt.where(Question.topic == topic)
    if difficulty_min is not None:
        stmt = stmt.where(Question.difficulty >= difficulty_min)
    if difficulty_max is not None:
        stmt = stmt.where(Question.difficulty <= difficulty_max)
        
    if randomize:
        stmt = stmt.order_by(func.random())
        
    stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()
