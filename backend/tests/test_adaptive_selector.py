"""
Tests for M4.3 — AdaptiveSelector.

Tests all three pipeline stages:
  - _compute_skill_gap: picks lowest mastery skill
  - _confidence_gate: terminates at threshold or budget
  - select_next_question: integration (mocked RAG engine)
"""

from unittest.mock import AsyncMock, MagicMock

from app.ai.rag_engine import GeneratedQuestion, GraphRAGEngine, RetrievedCandidate
from app.models.candidate import CandidateState, CompetencyNode
from app.services.adaptive_selector import (
    MASTERY_THRESHOLD,
    MAX_QUESTIONS_PER_SESSION,
    MIN_QUESTIONS_BEFORE_GATE,
    AdaptiveSelector,
)


def _make_state(masteries: dict[str, float] | None = None) -> CandidateState:
    """Create a CandidateState with configurable mastery values."""
    state = CandidateState(session_id="test-session")
    default_skills = {
        "python_basics": 0.5,
        "python_oop": 0.3,
        "data_structures": 0.1,
        "algorithms": 0.4,
        "system_design": 0.2,
    }
    for sid, mastery in (masteries or default_skills).items():
        state.skills[sid] = CompetencyNode(
            skill_id=sid,
            name=sid.replace("_", " ").title(),
            category="Lang",
            mastery_probability=mastery,
        )
    return state


def _make_selector(mock_retrieve=None) -> AdaptiveSelector:
    """Create an AdaptiveSelector with a fully mocked GraphRAGEngine."""
    mock_rag = MagicMock(spec=GraphRAGEngine)
    if mock_retrieve is not None:
        mock_rag.retrieve = mock_retrieve
    else:
        # Default: returns one candidate, no generation needed
        mock_rag.retrieve = AsyncMock(return_value=(
            [RetrievedCandidate(
                question_id="q1",
                document="What is a linked list?",
                topic="data_structures",
                difficulty=3,
                distance=0.05,
            )],
            None,
        ))
    return AdaptiveSelector(rag_engine=mock_rag)


# ─── _compute_skill_gap ───────────────────────────────────────────────────────


class TestComputeSkillGap:
    def test_picks_lowest_mastery_skill(self):
        selector = _make_selector()
        state = _make_state({"python_basics": 0.9, "data_structures": 0.1, "algorithms": 0.5})
        skill_id, _ = selector._compute_skill_gap(state)
        assert skill_id == "data_structures"

    def test_difficulty_increases_with_mastery(self):
        selector = _make_selector()
        lo_state = _make_state({"python_basics": 0.1})
        hi_state = _make_state({"python_basics": 0.8})

        _, lo_diff = selector._compute_skill_gap(lo_state)
        _, hi_diff = selector._compute_skill_gap(hi_state)
        assert lo_diff < hi_diff

    def test_empty_state_returns_default(self):
        selector = _make_selector()
        state = CandidateState(session_id="empty")
        skill_id, difficulty = selector._compute_skill_gap(state)
        assert isinstance(skill_id, str)
        assert 1 <= difficulty <= 10


# ─── _confidence_gate ─────────────────────────────────────────────────────────


class TestConfidenceGate:
    def test_does_not_trigger_before_min_questions(self):
        selector = _make_selector()
        state = _make_state({s: 0.95 for s in ["a", "b", "c"]})
        should_stop, _ = selector._confidence_gate(state, total_asked=2)
        assert not should_stop

    def test_triggers_when_mastery_above_threshold(self):
        selector = _make_selector()
        high_mastery = {f"s{i}": MASTERY_THRESHOLD + 0.01 for i in range(5)}
        state = _make_state(high_mastery)
        should_stop, reason = selector._confidence_gate(state, total_asked=MIN_QUESTIONS_BEFORE_GATE)
        assert should_stop
        assert "threshold" in reason.lower()

    def test_triggers_when_max_questions_reached(self):
        selector = _make_selector()
        state = _make_state({"s1": 0.1})
        should_stop, reason = selector._confidence_gate(state, total_asked=MAX_QUESTIONS_PER_SESSION)
        assert should_stop
        assert "budget" in reason.lower()

    def test_does_not_trigger_below_threshold(self):
        selector = _make_selector()
        state = _make_state({"s1": 0.5, "s2": 0.4})
        should_stop, _ = selector._confidence_gate(state, total_asked=5)
        assert not should_stop


# ─── select_next_question ─────────────────────────────────────────────────────


class TestSelectNextQuestion:
    async def test_returns_retrieved_candidate(self):
        selector = _make_selector()
        state = _make_state()
        result = await selector.select_next_question(state)
        assert not result.should_terminate
        assert result.db_question is not None
        assert result.db_question.question_id == "q1"

    async def test_returns_generated_when_retrieval_empty(self):
        gen_q = GeneratedQuestion(
            question_text="Explain OOP principles.",
            expected_answer="The four pillars are...",
            concepts=["encapsulation", "inheritance", "polymorphism"],
            difficulty=5,
            topic="python_oop",
        )
        mock_retrieve = AsyncMock(return_value=([], gen_q))
        selector = _make_selector(mock_retrieve=mock_retrieve)
        state = _make_state()
        result = await selector.select_next_question(state)
        assert not result.should_terminate
        assert result.generated_question is not None
        assert result.generated_question.question_text == gen_q.question_text

    async def test_terminates_when_gate_fires(self):
        selector = _make_selector()
        # High mastery state
        high_mastery = {f"s{i}": 0.95 for i in range(5)}
        state = _make_state(high_mastery)
        # Enough questions asked
        asked = [f"q{i}" for i in range(MIN_QUESTIONS_BEFORE_GATE)]
        result = await selector.select_next_question(state, asked_question_ids=asked)
        assert result.should_terminate

    async def test_question_text_property(self):
        selector = _make_selector()
        state = _make_state()
        result = await selector.select_next_question(state)
        assert isinstance(result.question_text, str)
        assert len(result.question_text) > 0
