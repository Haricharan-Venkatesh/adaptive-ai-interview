"""
Pydantic models for Answer Evaluation.

These models are used for evaluating candidate answers using the LLM client
and serializing the evaluation results.
"""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class EvaluationResult(BaseModel):
    """
    Structured output from the LLM after evaluating a candidate's answer.
    """
    correctness: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall technical correctness of the answer (0.0 to 1.0)"
    )
    reasoning_quality: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Quality and logical soundness of the candidate's reasoning"
    )
    explanation_depth: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Depth of the explanation provided by the candidate"
    )
    code_quality: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Quality, efficiency, and readability of the code (if applicable)"
    )
    communication_skills: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Clarity and effectiveness of communication"
    )
    concepts_mastered: list[str] = Field(
        default_factory=list,
        description="List of required concepts the candidate successfully demonstrated"
    )
    concepts_failed: list[str] = Field(
        default_factory=list,
        description="List of required concepts the candidate failed to demonstrate or missed"
    )
    feedback: str = Field(
        ...,
        description="Constructive, specific feedback explaining the score and how to improve"
    )
    
    # Optional fields for future extensibility
    overall_score: float | None = Field(
        default=None,
        description="Aggregated overall score across all metrics"
    )
    confidence: float | None = Field(
        default=None,
        description="Model's confidence in this evaluation"
    )
    next_topic: str | None = Field(
        default=None,
        description="Suggested next topic based on the candidate's performance"
    )


class AnswerSubmissionRequest(BaseModel):
    """
    Request model for a candidate submitting an answer to a question.
    """
    session_id: str = Field(
        ...,
        description="The ID of the active interview session"
    )
    question_id: str = Field(
        ...,
        description="The ID of the question being answered"
    )
    candidate_code: str | None = Field(
        default=None,
        description="The code written by the candidate (if applicable)"
    )
    candidate_text: str | None = Field(
        default=None,
        description="The text explanation or verbal transcript of the candidate's answer"
    )

    @model_validator(mode="after")
    def validate_content_provided(self) -> "AnswerSubmissionRequest":
        """Ensure that either candidate code or candidate text is provided."""
        has_code = self.candidate_code and self.candidate_code.strip()
        has_text = self.candidate_text and self.candidate_text.strip()
        
        if not has_code and not has_text:
            raise ValueError("At least one of candidate_code or candidate_text must be provided")
        return self


class NextAction(StrEnum):
    """Indicates the next action to take in the interview session."""
    CONTINUE = "continue"
    TERMINATE = "terminate"


class AnswerSubmissionResponse(BaseModel):
    """
    Response model returning the evaluation results to the client.
    """
    evaluation: EvaluationResult
    next_action: NextAction = Field(
        default=NextAction.CONTINUE,
        description="Indicates whether the interview should 'continue' or 'terminate'"
    )
