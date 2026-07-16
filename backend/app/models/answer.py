"""
Pydantic models for Answer Evaluation.

These models are used for evaluating candidate answers using the LLM client
and serializing the evaluation results.
"""

from pydantic import BaseModel, Field


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


class AnswerSubmissionResponse(BaseModel):
    """
    Response model returning the evaluation results to the client.
    """
    evaluation: EvaluationResult
    next_action: str = Field(
        default="continue",
        description="Indicates whether the interview should 'continue' or 'terminate'"
    )
