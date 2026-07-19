from enum import StrEnum

from pydantic import BaseModel, Field


class SkillLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class CompetencyNode(BaseModel):
    skill_id: str
    name: str
    category: str
    mastery_probability: float = Field(default=0.1, ge=0.0, le=1.0)
    confidence: float = Field(default=0.1, ge=0.0, le=1.0)
    questions_attempted: int = 0
    questions_correct: int = 0

class SkillEdge(BaseModel):
    source_id: str
    target_id: str
    weight: float = Field(default=1.0, ge=0.0)

class CandidateState(BaseModel):
    session_id: str
    overall_score: float = 0.0
    skills: dict[str, CompetencyNode] = Field(default_factory=dict)
