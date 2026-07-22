"""
Answer Analyzer Service.

This service evaluates a candidate's answer against the original question using the LLM.
It formats the evaluation prompt and parses the result into an EvaluationResult model.
"""

from pydantic import BaseModel, Field

from app.ai.llm_client import get_llm_client
from app.ai.prompts.answer_eval import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.core.logging import get_logger
from app.models.answer import EvaluationResult

logger = get_logger(__name__)


class _GeminiEvaluationResult(BaseModel):
    """
    Schema-safe version of EvaluationResult for Gemini's response_schema parameter.

    Contains non-optional required fields without numeric range constraints (ge/le)
    to prevent Pydantic from emitting 'minimum' and 'maximum' keywords into the JSON schema,
    which are unsupported by Google Gemini's Schema protobuf converter.
    """

    correctness: float = Field(description="Overall technical correctness (0.0 to 1.0)")
    reasoning_quality: float = Field(description="Quality and logical soundness of reasoning (0.0 to 1.0)")
    explanation_depth: float = Field(description="Depth of explanation (0.0 to 1.0)")
    code_quality: float = Field(description="Quality, efficiency, and readability of code (0.0 to 1.0)")
    communication_skills: float = Field(description="Clarity of communication (0.0 to 1.0)")
    concepts_mastered: list[str] = Field(description="Required concepts successfully demonstrated")
    concepts_failed: list[str] = Field(description="Required concepts failed or missed")
    feedback: str = Field(description="Constructive feedback explaining the score")


async def analyze_answer(
    topic: str,
    difficulty: int,
    question_text: str,
    required_concepts: list[str],
    reference_answer: str,
    candidate_code: str | None = None,
    candidate_text: str | None = None,
) -> EvaluationResult:
    """
    Evaluate a candidate's answer using the configured LLM.

    Args:
        topic: The topic domain of the question.
        difficulty: The difficulty level (1-10).
        question_text: The actual question asked.
        required_concepts: Key concepts expected in the answer.
        reference_answer: The ideal or expected answer.
        candidate_code: The code submitted by the candidate.
        candidate_text: The verbal or written explanation.

    Returns:
        EvaluationResult: Structured metrics and feedback.

    Raises:
        RuntimeError: If the LLM call fails (so the caller can decide how to handle it).
    """
    logger.info(
        "Analyzing candidate answer",
        topic=topic,
        difficulty=difficulty,
        has_code=bool(candidate_code),
        has_text=bool(candidate_text),
        question_length=len(question_text),
    )

    from app.services.ast_analyzer import analyze_code_ast

    ast_analysis_text = "No code provided for static analysis."
    if candidate_code:
        ast_result = analyze_code_ast(candidate_code)
        if ast_result["syntax_valid"]:
            ast_analysis_text = (
                f"Syntax: Valid\n"
                f"Functions: {ast_result['functions']}\n"
                f"Classes: {ast_result['classes']}\n"
                f"Imports: {ast_result['imports']}\n"
                f"Complexity (Nodes): {ast_result['num_nodes']}"
            )
        else:
            ast_analysis_text = f"Syntax: Invalid\nError: {ast_result['error_message']}"

    # Format the prompt
    prompt = USER_PROMPT_TEMPLATE.format(
        topic=topic,
        difficulty=difficulty,
        question_text=question_text,
        required_concepts=", ".join(required_concepts) if required_concepts else "None specified",
        reference_answer=reference_answer,
        candidate_code=candidate_code or "No code provided.",
        candidate_text=candidate_text or "No text provided.",
        ast_analysis=ast_analysis_text,
    )

    client = get_llm_client()
    logger.info(
        "Sending answer to Gemini for evaluation",
        llm_initialized=client.initialized,
        topic=topic,
        difficulty=difficulty,
    )

    # Use the schema-safe model for the Gemini call to avoid Optional field issues.
    gemini_result = await client.generate_json(
        prompt=prompt,
        response_model=_GeminiEvaluationResult,
        system_instruction=SYSTEM_PROMPT,
        temperature=0.2,
    )

    logger.info(
        "Answer evaluation completed via Gemini",
        correctness=gemini_result.correctness,
        reasoning_quality=gemini_result.reasoning_quality,
        concepts_mastered=gemini_result.concepts_mastered,
        concepts_failed=gemini_result.concepts_failed,
    )

    # Construct the full EvaluationResult (including optional extensibility fields)
    return EvaluationResult(
        correctness=gemini_result.correctness,
        reasoning_quality=gemini_result.reasoning_quality,
        explanation_depth=gemini_result.explanation_depth,
        code_quality=gemini_result.code_quality,
        communication_skills=gemini_result.communication_skills,
        concepts_mastered=gemini_result.concepts_mastered,
        concepts_failed=gemini_result.concepts_failed,
        feedback=gemini_result.feedback,
    )
