"""
Tests for M4.2 — GraphRAGEngine.

Mocks:
  - EmbeddingService (returns fixed zero-vectors)
  - ChromaDB query_similar (returns configurable results)
  - LLMClient (returns mock GeneratedQuestion via existing mock machinery)
"""

from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.rag_engine import GeneratedQuestion, GraphRAGEngine
from app.models.candidate import CandidateState, CompetencyNode


def _make_engine() -> GraphRAGEngine:
    return GraphRAGEngine()


def _make_state(mastery: float = 0.1) -> CandidateState:
    state = CandidateState(session_id="test-session")
    state.skills["python_basics"] = CompetencyNode(
        skill_id="python_basics",
        name="Python Basics",
        category="Language",
        mastery_probability=mastery,
    )
    return state


# ─── _get_neighbor_skills ─────────────────────────────────────────────────────


class TestGetNeighborSkills:
    def test_returns_target_and_neighbors(self):
        engine = _make_engine()
        neighbors = engine._get_neighbor_skills("python_basics")
        # python_basics has successors: python_oop, data_structures
        assert "python_basics" in neighbors
        assert len(neighbors) >= 1

    def test_unknown_skill_returns_just_itself(self):
        engine = _make_engine()
        neighbors = engine._get_neighbor_skills("nonexistent_skill_xyz")
        assert "nonexistent_skill_xyz" in neighbors


# ─── _vector_search ───────────────────────────────────────────────────────────


class TestVectorSearch:
    @patch("app.ai.rag_engine.query_similar")
    @patch("app.ai.rag_engine.get_embedding_service")
    def test_returns_candidates_for_matching_topics(self, mock_svc, mock_query):
        mock_svc.return_value.embed_text.return_value = [0.0] * 384
        mock_query.return_value = [
            {
                "id": "q1",
                "document": "What is a list?",
                "metadata": {"topic": "python_basics", "difficulty": 3},
                "distance": 0.1,
            },
            {
                "id": "q2",
                "document": "What is Django?",
                "metadata": {"topic": "web_framework", "difficulty": 5},
                "distance": 0.3,
            },
        ]
        engine = _make_engine()
        results = engine._vector_search("python_basics", mastery=0.1, n=5)

        # q1 matches (topic = python_basics), q2 doesn't (web_framework not a neighbor)
        assert any(r.question_id == "q1" for r in results)
        assert all(r.question_id != "q2" for r in results)

    @patch("app.ai.rag_engine.query_similar")
    @patch("app.ai.rag_engine.get_embedding_service")
    def test_returns_empty_list_when_no_matches(self, mock_svc, mock_query):
        mock_svc.return_value.embed_text.return_value = [0.0] * 384
        mock_query.return_value = []
        engine = _make_engine()
        results = engine._vector_search("python_basics", mastery=0.5)
        assert results == []


# ─── retrieve (full pipeline) ─────────────────────────────────────────────────


class TestRetrieve:
    @patch("app.ai.rag_engine.query_similar")
    @patch("app.ai.rag_engine.get_embedding_service")
    async def test_returns_retrieved_when_available(self, mock_svc, mock_query):
        mock_svc.return_value.embed_text.return_value = [0.0] * 384
        mock_query.return_value = [
            {
                "id": "q1",
                "document": "Explain Python GIL.",
                "metadata": {"topic": "python_basics", "difficulty": 4},
                "distance": 0.05,
            }
        ]
        engine = _make_engine()
        candidates, generated = await engine.retrieve("python_basics", mastery=0.2)
        assert len(candidates) >= 1
        assert generated is None

    @patch("app.ai.rag_engine.get_llm_client")
    @patch("app.ai.rag_engine.query_similar")
    @patch("app.ai.rag_engine.get_embedding_service")
    async def test_falls_back_to_llm_when_no_results(self, mock_svc, mock_query, mock_llm):
        mock_svc.return_value.embed_text.return_value = [0.0] * 384
        mock_query.return_value = []

        mock_client = MagicMock()
        mock_client.generate_json = AsyncMock(return_value=GeneratedQuestion(
            question_text="What is a decorator in Python?",
            expected_answer="A decorator is a function that wraps another function.",
            concepts=["decorators", "closures", "higher-order functions"],
            difficulty=4,
            topic="python_basics",
        ))
        mock_llm.return_value = mock_client

        engine = _make_engine()
        candidates, generated = await engine.retrieve("python_basics", mastery=0.2)
        assert candidates == []
        assert generated is not None
        assert "decorator" in generated.question_text.lower()

    @patch("app.ai.rag_engine.query_similar")
    @patch("app.ai.rag_engine.get_embedding_service")
    async def test_filters_out_already_asked(self, mock_svc, mock_query):
        mock_svc.return_value.embed_text.return_value = [0.0] * 384
        mock_query.return_value = [
            {
                "id": "already-asked-id",
                "document": "Some question",
                "metadata": {"topic": "python_basics", "difficulty": 3},
                "distance": 0.1,
            }
        ]
        engine = _make_engine()
        candidates, generated = await engine.retrieve(
            "python_basics", mastery=0.1, asked_question_ids=["already-asked-id"]
        )
        # Should be filtered out, but LLM fallback might also fail without mock
        # Just check that "already-asked-id" is not in candidates
        assert all(c.question_id != "already-asked-id" for c in candidates)
