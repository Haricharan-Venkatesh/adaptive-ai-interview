"""
Interview API — M4.3 Adaptive Question Selection.

Four endpoints drive the end-to-end interview loop:

  POST /interview/start                  — create session, serve first question
  POST /interview/{session_id}/answer    — submit answer, get next question or "done"
  GET  /interview/{session_id}/state     — inspect current candidate knowledge state
  POST /interview/{session_id}/end       — force-terminate and get final summary

Persistence strategy:
  CandidateState is serialised into the InterviewSession.metadata dict so it
  travels with the existing Redis session model. This avoids adding a new
  Redis key schema for Phase 4.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.ai.rag_engine import GeneratedQuestion
from app.core.logging import get_logger
from app.db.redis_client import get_redis
from app.models.candidate import CandidateState
from app.models.session import (
    CreateSessionRequest,
    InterviewSession,
    InterviewTopic,
    UpdateSessionRequest,
)
from app.services.adaptive_selector import (
    AdaptiveSelector,
    SelectionResult,
    get_adaptive_selector,
)
from app.services.answer_analyzer import analyze_answer
from app.services.session_service import (
    create_session,
    get_session,
    update_session,
)
from app.services.skill_graph import skill_graph_service

interview_router = APIRouter(tags=["interview"])
logger = get_logger(__name__)

# ─── Request / Response schemas ──────────────────────────────────────────────


class StartInterviewRequest(BaseModel):
    """Body for starting a new interview session."""

    candidate_name: str = Field(default="Anonymous", max_length=100)
    topic: str = Field(default="DSA", description="Interview topic (DSA, OOP, System Design, etc.)")
    difficulty_level: int = Field(default=5, ge=1, le=10)


class QuestionPayload(BaseModel):
    """A question presented to the candidate."""

    question_text: str
    topic: str
    difficulty: int
    concepts: list[str]
    source: str  # "retrieved" | "generated"
    question_id: str | None = None  # set for retrieved DB questions
    expected_answer: str = ""


class StartInterviewResponse(BaseModel):
    session_id: str
    message: str
    first_question: QuestionPayload


class AnswerSubmissionRequest(BaseModel):
    """Candidate's submitted answer."""

    candidate_text: str | None = Field(default=None)
    candidate_code: str | None = Field(default=None)
    question_text: str = Field(description="The exact question that was answered")
    question_topic: str
    question_difficulty: int
    question_concepts: list[str] = Field(default_factory=list)
    expected_answer: str = Field(default="")


class AnswerResponse(BaseModel):
    """Result of evaluating an answer — includes next question or termination signal."""

    session_id: str
    evaluation: dict[str, Any]
    interview_complete: bool
    termination_reason: str = ""
    next_question: QuestionPayload | None = None
    questions_asked: int


class InterviewStateResponse(BaseModel):
    session_id: str
    candidate_state: dict[str, Any]
    questions_asked: int
    overall_score: float


class InterviewSummaryResponse(BaseModel):
    session_id: str
    questions_asked: int
    overall_score: float
    skill_summary: list[dict[str, Any]]
    termination_reason: str


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _result_to_payload(result: SelectionResult) -> QuestionPayload:
    """Convert a SelectionResult into a wire-format QuestionPayload."""
    if result.db_question:
        c = result.db_question
        return QuestionPayload(
            question_text=c.document,
            topic=c.topic,
            difficulty=c.difficulty,
            concepts=[],
            source="retrieved",
            question_id=c.question_id,
        )

    g: GeneratedQuestion = result.generated_question  # type: ignore[assignment]
    return QuestionPayload(
        question_text=g.question_text,
        topic=g.topic,
        difficulty=g.difficulty,
        concepts=g.concepts,
        source="generated",
        question_id=None,
        expected_answer=g.expected_answer,
    )


def _extract_adaptive_state(session: InterviewSession) -> dict[str, Any]:
    """Extract our Phase 4 adaptive state from session.metadata."""
    return session.metadata.get("adaptive", {})


def _build_candidate_state(session: InterviewSession) -> CandidateState:
    """Reconstruct CandidateState from the InterviewSession.metadata."""
    raw = _extract_adaptive_state(session).get("candidate_state")
    if raw:
        return CandidateState.model_validate(raw)
    return skill_graph_service.initialize_candidate_state(session.session_id)


def _compute_overall_score(state: CandidateState) -> float:
    if not state.skills:
        return 0.0
    return sum(n.mastery_probability for n in state.skills.values()) / len(state.skills)


def _map_topic_to_interview_topic(topic: str) -> InterviewTopic:
    """Best-effort mapping from free-text topic to InterviewTopic enum."""
    mapping = {
        "dsa": InterviewTopic.DSA,
        "system design": InterviewTopic.SYSTEM_DESIGN,
        "oop": InterviewTopic.OOP,
        "object oriented": InterviewTopic.OOP,
        "dbms": InterviewTopic.DBMS,
        "database": InterviewTopic.DBMS,
        "os": InterviewTopic.OS_NETWORKS,
        "operating system": InterviewTopic.OS_NETWORKS,
        "behavioral": InterviewTopic.BEHAVIORAL,
    }
    return mapping.get(topic.lower(), InterviewTopic.DOMAIN_SPECIFIC)


# ─── Endpoints ───────────────────────────────────────────────────────────────


@interview_router.post("/start", response_model=StartInterviewResponse, status_code=201)
async def start_interview(
    body: StartInterviewRequest,
    redis=Depends(get_redis),
    selector: AdaptiveSelector = Depends(get_adaptive_selector),
) -> StartInterviewResponse:
    """
    Create a new interview session and serve the first question.

    The candidate's knowledge state is initialised using the BKT priors
    from the skill graph and stored in Redis via the InterviewSession.metadata.
    """
    interview_topic = _map_topic_to_interview_topic(body.topic)

    create_req = CreateSessionRequest(
        candidate_id=body.candidate_name,
        topic=interview_topic,
        difficulty_level=body.difficulty_level,
    )
    session = await create_session(redis, create_req)
    session_id = session.session_id

    # Initialise candidate state from skill graph BKT priors
    state = skill_graph_service.initialize_candidate_state(session_id)

    # Select the first question
    result = await selector.select_next_question(
        state=state,
        asked_question_ids=[],
        asked_titles=[],
    )

    if result.should_terminate:
        raise HTTPException(status_code=500, detail="No questions available to start interview")

    first_q = _result_to_payload(result)

    # Persist adaptive state into session.metadata
    asked_ids = [first_q.question_id] if first_q.question_id else []
    asked_titles = [first_q.question_text[:80]]

    adaptive_meta = {
        "candidate_state": state.model_dump(),
        "asked_question_ids": asked_ids,
        "asked_titles": asked_titles,
        "questions_asked": 1,
    }
    update_req = UpdateSessionRequest(metadata={"adaptive": adaptive_meta})
    await update_session(redis, session_id, update_req)

    logger.info(
        "Interview started",
        session_id=session_id,
        candidate=body.candidate_name,
        first_topic=first_q.topic,
    )

    return StartInterviewResponse(
        session_id=session_id,
        message=f"Interview started for {body.candidate_name}",
        first_question=first_q,
    )


@interview_router.post("/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(
    session_id: str,
    body: AnswerSubmissionRequest,
    redis=Depends(get_redis),
    selector: AdaptiveSelector = Depends(get_adaptive_selector),
) -> AnswerResponse:
    """
    Submit an answer to the current question.

    Evaluates the answer via LLM, updates the candidate's knowledge state,
    then runs the adaptive selector to return the next question — or signals
    interview completion.
    """
    session = await get_session(redis, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    state = _build_candidate_state(session)
    adaptive = _extract_adaptive_state(session)
    asked_ids: list[str] = adaptive.get("asked_question_ids", [])
    asked_titles: list[str] = adaptive.get("asked_titles", [])
    questions_asked: int = adaptive.get("questions_asked", 1)

    # ── Evaluate answer ────────────────────────────────────────────────────────
    evaluation = await analyze_answer(
        topic=body.question_topic,
        difficulty=body.question_difficulty,
        question_text=body.question_text,
        required_concepts=body.question_concepts,
        reference_answer=body.expected_answer,
        candidate_code=body.candidate_code,
        candidate_text=body.candidate_text,
    )

    is_correct = evaluation.correctness >= 0.6

    # ── Update skill state ─────────────────────────────────────────────────────
    state = skill_graph_service.update_skill(
        candidate_state=state,
        skill_id=body.question_topic,
        is_correct=is_correct,
    )
    state.overall_score = _compute_overall_score(state)

    # ── Select next question ───────────────────────────────────────────────────
    result = await selector.select_next_question(
        state=state,
        asked_question_ids=asked_ids,
        asked_titles=asked_titles,
    )

    next_q: QuestionPayload | None = None
    if not result.should_terminate:
        next_q = _result_to_payload(result)
        if next_q.question_id:
            asked_ids.append(next_q.question_id)
        asked_titles.append(next_q.question_text[:80])
        questions_asked += 1

    # ── Persist updated state ─────────────────────────────────────────────────
    adaptive_meta = {
        "candidate_state": state.model_dump(),
        "asked_question_ids": asked_ids,
        "asked_titles": asked_titles,
        "questions_asked": questions_asked,
    }
    update_req = UpdateSessionRequest(metadata={"adaptive": adaptive_meta})
    await update_session(redis, session_id, update_req)

    logger.info(
        "Answer evaluated",
        session_id=session_id,
        topic=body.question_topic,
        correctness=evaluation.correctness,
        interview_complete=result.should_terminate,
    )

    return AnswerResponse(
        session_id=session_id,
        evaluation=evaluation.model_dump(),
        interview_complete=result.should_terminate,
        termination_reason=result.termination_reason if result.should_terminate else "",
        next_question=next_q,
        questions_asked=questions_asked,
    )


@interview_router.get("/{session_id}/state", response_model=InterviewStateResponse)
async def get_interview_state(
    session_id: str,
    redis=Depends(get_redis),
) -> InterviewStateResponse:
    """Return the candidate's current knowledge state for the given session."""
    session = await get_session(redis, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    state = _build_candidate_state(session)
    adaptive = _extract_adaptive_state(session)
    questions_asked: int = adaptive.get("questions_asked", 0)

    return InterviewStateResponse(
        session_id=session_id,
        candidate_state=state.model_dump(),
        questions_asked=questions_asked,
        overall_score=_compute_overall_score(state),
    )


@interview_router.post("/{session_id}/end", response_model=InterviewSummaryResponse)
async def end_interview(
    session_id: str,
    redis=Depends(get_redis),
) -> InterviewSummaryResponse:
    """
    Force-terminate an interview session and return a final performance summary.

    The summary includes per-skill mastery and an overall score.
    """
    session = await get_session(redis, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    state = _build_candidate_state(session)
    adaptive = _extract_adaptive_state(session)
    questions_asked: int = adaptive.get("questions_asked", 0)

    skill_summary = [
        {
            "skill_id": sid,
            "name": node.name,
            "mastery_probability": round(node.mastery_probability, 3),
            "questions_attempted": node.questions_attempted,
            "questions_correct": node.questions_correct,
            "accuracy": (
                round(node.questions_correct / node.questions_attempted, 2)
                if node.questions_attempted > 0
                else 0.0
            ),
        }
        for sid, node in state.skills.items()
    ]

    logger.info(
        "Interview ended",
        session_id=session_id,
        questions_asked=questions_asked,
        overall_score=_compute_overall_score(state),
    )

    return InterviewSummaryResponse(
        session_id=session_id,
        questions_asked=questions_asked,
        overall_score=round(_compute_overall_score(state), 3),
        skill_summary=skill_summary,
        termination_reason="Manually terminated by caller",
    )
