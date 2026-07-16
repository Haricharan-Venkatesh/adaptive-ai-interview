"""
Answer Analyzer Service.

This service evaluates a candidate's answer against the original question using the LLM.
It formats the evaluation prompt and parses the result into an EvaluationResult model.
"""

from app.ai.llm_client import get_llm_client
from app.ai.prompts.answer_eval import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.core.logging import get_logger
from app.models.answer import EvaluationResult

logger = get_logger(__name__)


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
    """
    logger.info(
        "Analyzing candidate answer",
        topic=topic,
        difficulty=difficulty,
        has_code=bool(candidate_code),
        has_text=bool(candidate_text),
    )

    # Format the prompt
    prompt = USER_PROMPT_TEMPLATE.format(
        topic=topic,
        difficulty=difficulty,
        question_text=question_text,
        required_concepts=", ".join(required_concepts) if required_concepts else "None specified",
        reference_answer=reference_answer,
        candidate_code=candidate_code or "No code provided.",
        candidate_text=candidate_text or "No text provided.",
    )

    client = get_llm_client()
    
    try:
        evaluation = await client.generate_json(
            prompt=prompt,
            response_model=EvaluationResult,
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
        )
        logger.info(
            "Answer evaluation completed",
            correctness=evaluation.correctness,
            concepts_mastered=len(evaluation.concepts_mastered),
            concepts_failed=len(evaluation.concepts_failed),
        )
        return evaluation
    except Exception as exc:
        logger.error(
            "Answer evaluation failed",
            error=str(exc),
        )
        raise
