"""
API routes for answering questions and evaluating them.
"""

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.postgres import get_db_session
from app.db.redis_client import get_redis
from app.models.answer import AnswerSubmissionRequest, AnswerSubmissionResponse
from app.services import answer_analyzer, session_service
from app.services.question_engine import get_question

logger = get_logger(__name__)

router = APIRouter(prefix="/answers", tags=["answers"])


@router.post("", response_model=AnswerSubmissionResponse)
async def submit_answer(
    request: AnswerSubmissionRequest,
    redis: Redis = Depends(get_redis),  # noqa: B008
    db: AsyncSession = Depends(get_db_session),  # noqa: B008
) -> AnswerSubmissionResponse:
    """
    Submit an answer for evaluation.
    
    1. Retrieves session from Redis and question from PostgreSQL.
    2. Calls the LLM Answer Analyzer.
    3. Updates the session history with the evaluation results.
    """
    logger.info("Processing answer submission", session_id=request.session_id, question_id=request.question_id)

    # 1. Fetch session
    session = await session_service.get_session(redis, request.session_id)
    if not session:
        logger.warning("Session not found", session_id=request.session_id)
        raise HTTPException(status_code=404, detail="Session not found or expired")
        
    # 2. Fetch the question details
    question = await get_question(db, request.question_id)
    if not question:
        logger.warning("Question not found", question_id=request.question_id)
        raise HTTPException(status_code=404, detail="Question not found")
        
    # 3. Analyze the answer via LLM
    question_full_text = f"{question.title}\n{question.question}"
    
    try:
        evaluation = await answer_analyzer.analyze_answer(
            topic=question.topic,
            difficulty=question.difficulty,
            question_text=question_full_text,
            required_concepts=question.concepts,
            reference_answer=question.expected_answer,
            candidate_code=request.candidate_code,
            candidate_text=request.candidate_text,
        )
    except Exception as exc:
        logger.error("Error during answer analysis", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to evaluate answer") from exc

    # 4. Update the session with the answer and evaluation
    # Find the question in history and update it
    updated_history = session.question_history.copy()
    found = False
    
    for i in reversed(range(len(updated_history))):
        if updated_history[i].question_id == request.question_id:
            updated_history[i].answer_text = request.candidate_text
            updated_history[i].score = evaluation.correctness
            updated_history[i].feedback = evaluation.feedback
            found = True
            break
            
    if not found:
        # If it wasn't already in history (e.g. out of order API calls), add it
        from app.models.session import QuestionRecord
        record = QuestionRecord(
            question_id=request.question_id,
            question_text=question.question,
            topic=question.topic,
            difficulty=question.difficulty,
            answer_text=request.candidate_text,
            score=evaluation.correctness,
            feedback=evaluation.feedback,
        )
        updated_history.append(record)
        
    session.question_history = updated_history
    session.total_questions_asked = len(updated_history)
    session.current_question_index = len(updated_history)
    
    # Save the updated session back to Redis directly to bypass UpdateSessionRequest limits
    from app.core.config import settings
    remaining_ttl = await redis.ttl(f"session:{request.session_id}")
    ttl = remaining_ttl if remaining_ttl > 0 else settings.session_ttl_seconds
    await redis.set(f"session:{request.session_id}", session.model_dump_json(), ex=ttl)
    logger.info(
        "Session updated with answer evaluation",
        session_id=request.session_id,
        total_questions_asked=session.total_questions_asked,
    )
    
    # Return response
    return AnswerSubmissionResponse(
        evaluation=evaluation,
        next_action="continue"
    )
