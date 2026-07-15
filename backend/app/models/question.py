"""
Question models for database and API.

Contains:
  - SQLAlchemy ORM model (Question)
  - Pydantic schemas (QuestionBase, QuestionCreate, QuestionUpdate, QuestionResponse)
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base

# ── SQLAlchemy ORM Model ──────────────────────────────────────────────────────

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String, nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String, nullable=False, index=True)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    concepts: Mapped[list[str]] = mapped_column(JSON, default=list)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    expected_answer: Mapped[str] = mapped_column(Text, nullable=False)
    sample_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    hints: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ── Pydantic API Schemas ──────────────────────────────────────────────────────

class QuestionBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    question: str = Field(min_length=1)
    topic: str = Field(min_length=1, max_length=100)
    difficulty: int = Field(ge=1, le=10)
    concepts: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    expected_answer: str = Field(min_length=1)
    sample_code: str | None = Field(default=None)
    language: str | None = Field(default=None)
    hints: list[str] = Field(default_factory=list)


class QuestionCreate(QuestionBase):
    """Schema for creating a new question."""
    pass


class QuestionUpdate(BaseModel):
    """Schema for partially updating a question."""
    title: str | None = Field(default=None, min_length=1, max_length=255)
    question: str | None = Field(default=None, min_length=1)
    topic: str | None = Field(default=None, min_length=1, max_length=100)
    difficulty: int | None = Field(default=None, ge=1, le=10)
    concepts: list[str] | None = Field(default=None)
    tags: list[str] | None = Field(default=None)
    expected_answer: str | None = Field(default=None, min_length=1)
    sample_code: str | None = Field(default=None)
    language: str | None = Field(default=None)
    hints: list[str] | None = Field(default=None)


class QuestionResponse(QuestionBase):
    """Schema for returning question data from the API."""
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
