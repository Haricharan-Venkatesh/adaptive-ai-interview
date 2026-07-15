"""
Pydantic models for Interview Session management.

These models serve three roles:
  1. API request/response validation (FastAPI route layer)
  2. Redis serialization (stored as JSON strings via model_dump_json)
  3. Business logic types used by session_service.py

Design decisions:
  - InterviewSession is the canonical domain model
  - CreateSessionRequest / UpdateSessionRequest are separate input models (SRP)
  - AppendQuestionRequest represents adding one Q&A record to session history
  - All datetimes are UTC-aware (timezone=UTC)
"""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ── Enums ─────────────────────────────────────────────────────────────────────

class SessionStatus(StrEnum):
    """Lifecycle status of an interview session."""

    ACTIVE = "active"           # Interview in progress
    PAUSED = "paused"           # Temporarily paused (future: reconnect)
    COMPLETED = "completed"     # Interview finished, report generated
    EXPIRED = "expired"         # TTL elapsed before completion


class InterviewTopic(StrEnum):
    """Topic domains available for an interview session."""

    DSA = "DSA"
    SYSTEM_DESIGN = "System Design"
    OOP = "OOP"
    DBMS = "DBMS"
    OS_NETWORKS = "OS & Networks"
    BEHAVIORAL = "Behavioral"
    DOMAIN_SPECIFIC = "Domain Specific"


# ── Sub-models ────────────────────────────────────────────────────────────────

class QuestionRecord(BaseModel):
    """
    A single question-answer record within an interview session.

    Appended to session.question_history after each exchange.
    """

    question_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique ID for this question instance",
    )
    question_text: str = Field(description="The question presented to the candidate")
    topic: str = Field(description="Skill topic of this question")
    difficulty: int = Field(ge=1, le=10, description="Question difficulty (1=easy, 10=hard)")
    answer_text: str | None = Field(default=None, description="Candidate's answer")
    score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Evaluation score (0.0 = wrong, 1.0 = perfect)",
    )
    feedback: str | None = Field(
        default=None,
        description="LLM-generated feedback on the answer",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp when this record was created",
    )


# ── Core domain model ─────────────────────────────────────────────────────────

class InterviewSession(BaseModel):
    """
    The canonical interview session model.

    Stored in Redis as a JSON string under key:  session:{session_id}
    Expires automatically after SESSION_TTL_SECONDS (default: 1 hour).
    """

    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID4 session identifier",
    )
    candidate_id: str = Field(description="Identifier of the candidate being interviewed")
    topic: InterviewTopic = Field(description="Primary interview topic domain")
    difficulty_level: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Starting difficulty level (adaptive engine will adjust)",
    )
    status: SessionStatus = Field(
        default=SessionStatus.ACTIVE,
        description="Current lifecycle status of the session",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp when the session was created",
    )
    expires_at: datetime = Field(
        description="UTC timestamp when the session will expire in Redis",
    )
    question_history: list[QuestionRecord] = Field(
        default_factory=list,
        description="Ordered list of all questions asked so far",
    )
    competency_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Per-skill competency scores (0.0–1.0), updated after each answer",
    )
    current_question_index: int = Field(
        default=0,
        ge=0,
        description="Index of the current question in question_history",
    )
    total_questions_asked: int = Field(
        default=0,
        ge=0,
        description="Total number of questions asked in this session",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary key-value metadata (e.g. recruiter notes, tags)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "candidate_id": "user_123",
                "topic": "DSA",
                "difficulty_level": 5,
                "status": "active",
                "created_at": "2025-01-01T10:00:00Z",
                "expires_at": "2025-01-01T11:00:00Z",
                "question_history": [],
                "competency_scores": {},
                "current_question_index": 0,
                "total_questions_asked": 0,
                "metadata": {},
            }
        }
    }


# ── API input models ──────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    """Request body for POST /api/v1/sessions."""

    candidate_id: str = Field(
        min_length=1,
        description="Identifier for the candidate (GitHub username, email, UUID, etc.)",
    )
    topic: InterviewTopic = Field(description="Interview topic domain")
    difficulty_level: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Starting difficulty (1=beginner, 10=expert)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata attached to this session",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "candidate_id": "haricharan_v",
                "topic": "DSA",
                "difficulty_level": 5,
            }
        }
    }


class UpdateSessionRequest(BaseModel):
    """
    Request body for PATCH /api/v1/sessions/{session_id}.

    All fields are optional — only provided fields are updated.
    This follows the HTTP PATCH semantics (partial update).
    """

    status: SessionStatus | None = Field(default=None)
    difficulty_level: int | None = Field(default=None, ge=1, le=10)
    competency_scores: dict[str, float] | None = Field(default=None)
    current_question_index: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] | None = Field(default=None)


class AppendQuestionRequest(BaseModel):
    """Request body for POST /api/v1/sessions/{session_id}/questions."""

    question_text: str = Field(min_length=1, description="The question text")
    topic: str = Field(description="Skill topic of the question")
    difficulty: int = Field(ge=1, le=10, description="Question difficulty")
    answer_text: str | None = Field(default=None, description="Candidate answer (optional)")
    score: float | None = Field(default=None, ge=0.0, le=1.0, description="Evaluation score")
    feedback: str | None = Field(default=None, description="LLM feedback")

    model_config = {
        "json_schema_extra": {
            "example": {
                "question_text": "Explain the difference between BFS and DFS.",
                "topic": "Graph Traversal",
                "difficulty": 4,
                "answer_text": "BFS uses a queue while DFS uses a stack...",
                "score": 0.85,
                "feedback": "Good explanation of the core difference.",
            }
        }
    }
