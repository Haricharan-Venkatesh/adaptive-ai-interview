"""
Adaptive Question Selector — M4.3.

This is the core intelligence of Phase 4. It implements the full pipeline
described in Architecture Modules 2.4, 2.5, and 2.6:

  2.4 Adaptive Question Selection  — skill-gap analysis + difficulty targeting
  2.5 Current Confidence Gate      — decide when to stop interviewing
  2.6 Next Question Generation     — delegate to GraphRAGEngine

The selector is state-free; it reads CandidateState and returns the next action.
"""

from __future__ import annotations

from app.ai.rag_engine import GeneratedQuestion, GraphRAGEngine, RetrievedCandidate, get_rag_engine
from app.core.logging import get_logger
from app.models.candidate import CandidateState
from app.models.question import QuestionResponse

logger = get_logger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

# Stop interviewing when average mastery exceeds this threshold
MASTERY_THRESHOLD: float = 0.80

# Stop when this many questions have been asked regardless of mastery
MAX_QUESTIONS_PER_SESSION: int = 15

# Minimum questions before the confidence gate can fire
MIN_QUESTIONS_BEFORE_GATE: int = 3


# ─── Output types ────────────────────────────────────────────────────────────


class SelectionResult:
    """
    Encapsulates the result of one selection step.

    Exactly one of `db_question` or `generated_question` is populated.
    `should_terminate` is True when the confidence gate fires.
    """

    def __init__(
        self,
        db_question: RetrievedCandidate | None = None,
        generated_question: GeneratedQuestion | None = None,
        should_terminate: bool = False,
        target_skill_id: str = "",
        target_difficulty: int = 5,
        termination_reason: str = "",
    ) -> None:
        self.db_question = db_question
        self.generated_question = generated_question
        self.should_terminate = should_terminate
        self.target_skill_id = target_skill_id
        self.target_difficulty = target_difficulty
        self.termination_reason = termination_reason

    @property
    def question_text(self) -> str:
        """Return the actual question text regardless of source."""
        if self.db_question:
            return self.db_question.document
        if self.generated_question:
            return self.generated_question.question_text
        return ""

    @property
    def question_source(self) -> str:
        return "retrieved" if self.db_question else "generated"


# ─── AdaptiveSelector ─────────────────────────────────────────────────────────


class AdaptiveSelector:
    """
    Stateless service that drives the adaptive interview loop.

    All methods are pure functions of (CandidateState, session_history).
    This makes unit testing trivial without needing DB connections.
    """

    def __init__(self, rag_engine: GraphRAGEngine) -> None:
        self._rag = rag_engine

    # ── Module 2.4: Skill Gap Analysis ────────────────────────────────────────

    def _compute_skill_gap(
        self, state: CandidateState
    ) -> tuple[str, int]:
        """
        Identify the skill with the largest knowledge gap and compute difficulty.

        Strategy:
          - Pick the skill with lowest mastery_probability
          - Difficulty is inverse of mastery: low mastery → easier questions first
            (Vygotsky zone of proximal development)

        Returns:
            (skill_id, target_difficulty) where difficulty is 1–10.
        """
        if not state.skills:
            return "python_basics", 3  # sensible default

        # Sort by mastery ascending — most needed first
        sorted_skills = sorted(
            state.skills.items(),
            key=lambda kv: kv[1].mastery_probability,
        )
        target_skill_id, target_node = sorted_skills[0]

        # Difficulty scales with mastery: 0% mastery → difficulty 3, 90% → difficulty 9
        mastery = target_node.mastery_probability
        difficulty = max(1, min(10, int(mastery * 10) + 3))

        logger.debug(
            "Skill gap computed",
            skill=target_skill_id,
            mastery=f"{mastery:.2%}",
            difficulty=difficulty,
        )
        return target_skill_id, difficulty

    # ── Module 2.5: Confidence Gate ────────────────────────────────────────────

    def _confidence_gate(
        self, state: CandidateState, total_asked: int
    ) -> tuple[bool, str]:
        """
        Decide whether there is enough evidence to terminate the interview.

        Returns:
            (should_terminate, reason_string)
        """
        if not state.skills:
            return False, ""

        # Hard cap on questions
        if total_asked >= MAX_QUESTIONS_PER_SESSION:
            return True, f"Question budget exhausted ({MAX_QUESTIONS_PER_SESSION} questions)"

        # Need at least MIN_QUESTIONS before we can judge mastery
        if total_asked < MIN_QUESTIONS_BEFORE_GATE:
            return False, ""

        avg_mastery = sum(n.mastery_probability for n in state.skills.values()) / len(state.skills)

        if avg_mastery >= MASTERY_THRESHOLD:
            return True, f"Mastery threshold reached (avg={avg_mastery:.0%} ≥ {MASTERY_THRESHOLD:.0%})"

        return False, ""

    # ── Module 2.6: Retrieval + Generation ────────────────────────────────────

    async def select_next_question(
        self,
        state: CandidateState,
        asked_question_ids: list[str] | None = None,
        asked_titles: list[str] | None = None,
    ) -> SelectionResult:
        """
        Full adaptive selection pipeline (Modules 2.4 → 2.5 → 2.6).

        Args:
            state: Current CandidateState with per-skill mastery values.
            asked_question_ids: ChromaDB/PG IDs already shown to candidate.
            asked_titles: Question titles shown (for LLM fallback de-duplication).

        Returns:
            SelectionResult with either a retrieved or generated question,
            or should_terminate=True if the interview should end.
        """
        total_asked = len(asked_question_ids or [])

        # ── 2.5: Gate first ────────────────────────────────────────────────────
        should_stop, reason = self._confidence_gate(state, total_asked)
        if should_stop:
            logger.info("Confidence gate fired — interview complete", reason=reason)
            return SelectionResult(should_terminate=True, termination_reason=reason)

        # ── 2.4: Identify skill gap ────────────────────────────────────────────
        skill_id, difficulty = self._compute_skill_gap(state)
        mastery = state.skills[skill_id].mastery_probability if skill_id in state.skills else 0.1

        # ── 2.6: Retrieve or generate ─────────────────────────────────────────
        candidates, generated = await self._rag.retrieve(
            skill_id=skill_id,
            mastery=mastery,
            n=5,
            difficulty_target=difficulty,
            asked_question_ids=asked_question_ids,
            asked_titles=asked_titles,
        )

        if candidates:
            chosen = candidates[0]  # highest similarity (lowest cosine distance)
            logger.info(
                "Adaptive selection: retrieved question",
                skill=skill_id,
                question_id=chosen.question_id,
                distance=round(chosen.distance, 3),
            )
            return SelectionResult(
                db_question=chosen,
                target_skill_id=skill_id,
                target_difficulty=difficulty,
            )

        # LLM fallback
        logger.info(
            "Adaptive selection: using LLM-generated question",
            skill=skill_id,
            difficulty=difficulty,
        )
        return SelectionResult(
            generated_question=generated,
            target_skill_id=skill_id,
            target_difficulty=difficulty,
        )


# ─── Singleton & FastAPI dependency ──────────────────────────────────────────

_selector: AdaptiveSelector | None = None


def get_adaptive_selector() -> AdaptiveSelector:
    """Return the module-level AdaptiveSelector singleton."""
    global _selector
    if _selector is None:
        _selector = AdaptiveSelector(rag_engine=get_rag_engine())
        logger.info("AdaptiveSelector singleton created")
    return _selector
