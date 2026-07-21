"""
Tests for M4.3 — Interview API endpoints.

Uses httpx.AsyncClient + fakeredis to run full round-trips without
any real external services (no Redis, Postgres, Neo4j, or LLM API).

All Phase 4 dependencies are mocked:
  - EmbeddingService (skipped, chroma not initialized in test app)
  - ChromaDB (EphemeralClient via init_chroma(testing=True))
  - AdaptiveSelector (returns canned results via AsyncMock)
  - LLM (returns mock EvaluationResult via existing mock machinery)
"""

from unittest.mock import AsyncMock, MagicMock

import fakeredis.aioredis as fakeredis
import httpx
import pytest

from app.ai.rag_engine import GeneratedQuestion, RetrievedCandidate
from app.services.adaptive_selector import SelectionResult

# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture()
def fake_redis():
    return fakeredis.FakeRedis()


@pytest.fixture()
def fake_retrieval_result() -> SelectionResult:
    """A SelectionResult that returns a canned retrieved question."""
    return SelectionResult(
        db_question=RetrievedCandidate(
            question_id="q-test-001",
            document="What is a linked list?",
            topic="data_structures",
            difficulty=3,
            distance=0.05,
        ),
        target_skill_id="data_structures",
        target_difficulty=3,
    )


@pytest.fixture()
def fake_generated_result() -> SelectionResult:
    """A SelectionResult that uses an LLM-generated question."""
    return SelectionResult(
        generated_question=GeneratedQuestion(
            question_text="Explain Python decorators.",
            expected_answer="Decorators wrap another function.",
            concepts=["closures", "higher-order functions", "syntactic sugar"],
            difficulty=4,
            topic="python_basics",
        ),
        target_skill_id="python_basics",
        target_difficulty=4,
    )


@pytest.fixture()
def app_with_mocks(fake_redis, fake_retrieval_result):
    """Build a test FastAPI app with all external deps mocked."""
    from app.db.redis_client import get_redis
    from app.main import create_app
    from app.services.adaptive_selector import get_adaptive_selector

    test_app = create_app()

    # Override Redis
    test_app.dependency_overrides[get_redis] = lambda: fake_redis

    # Override AdaptiveSelector
    mock_selector = MagicMock()
    mock_selector.select_next_question = AsyncMock(return_value=fake_retrieval_result)
    test_app.dependency_overrides[get_adaptive_selector] = lambda: mock_selector

    return test_app


# ─── POST /interview/start ────────────────────────────────────────────────────


class TestStartInterview:
    async def test_start_returns_201_with_session_and_question(self, app_with_mocks):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app_with_mocks), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/interview/start",
                json={"candidate_name": "Alice", "topic": "DSA", "difficulty_level": 5},
            )
        assert resp.status_code == 201
        body = resp.json()
        assert "session_id" in body
        assert "first_question" in body
        fq = body["first_question"]
        assert fq["question_text"]
        assert fq["source"] in ("retrieved", "generated")

    async def test_start_default_values(self, app_with_mocks):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app_with_mocks), base_url="http://test"
        ) as client:
            resp = await client.post("/api/v1/interview/start", json={})
        assert resp.status_code == 201


# ─── POST /interview/{session_id}/answer ─────────────────────────────────────


class TestSubmitAnswer:
    async def test_submit_answer_returns_next_question(self, app_with_mocks):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app_with_mocks), base_url="http://test"
        ) as client:
            # Start interview first
            start_resp = await client.post(
                "/api/v1/interview/start",
                json={"candidate_name": "Bob", "topic": "DSA"},
            )
            assert start_resp.status_code == 201
            session_id = start_resp.json()["session_id"]

            # Submit an answer
            answer_resp = await client.post(
                f"/api/v1/interview/{session_id}/answer",
                json={
                    "candidate_text": "A linked list is a sequence of nodes.",
                    "question_text": "What is a linked list?",
                    "question_topic": "data_structures",
                    "question_difficulty": 3,
                    "question_concepts": ["nodes", "pointers"],
                    "expected_answer": "A linked list stores elements as nodes with pointers.",
                },
            )
        assert answer_resp.status_code == 200
        body = answer_resp.json()
        assert "evaluation" in body
        assert "interview_complete" in body
        assert body["questions_asked"] >= 1

    async def test_submit_answer_to_missing_session_returns_404(self, app_with_mocks):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app_with_mocks), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/interview/nonexistent-session-id/answer",
                json={
                    "candidate_text": "some answer",
                    "question_text": "Q",
                    "question_topic": "python_basics",
                    "question_difficulty": 3,
                },
            )
        assert resp.status_code == 404


# ─── GET /interview/{session_id}/state ───────────────────────────────────────


class TestGetInterviewState:
    async def test_get_state_returns_candidate_state(self, app_with_mocks):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app_with_mocks), base_url="http://test"
        ) as client:
            start_resp = await client.post(
                "/api/v1/interview/start",
                json={"candidate_name": "Carol"},
            )
            session_id = start_resp.json()["session_id"]

            state_resp = await client.get(f"/api/v1/interview/{session_id}/state")
        assert state_resp.status_code == 200
        body = state_resp.json()
        assert body["session_id"] == session_id
        assert "candidate_state" in body
        assert "overall_score" in body

    async def test_get_state_missing_session_returns_404(self, app_with_mocks):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app_with_mocks), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/interview/bad-session/state")
        assert resp.status_code == 404


# ─── POST /interview/{session_id}/end ────────────────────────────────────────


class TestEndInterview:
    async def test_end_returns_summary(self, app_with_mocks):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app_with_mocks), base_url="http://test"
        ) as client:
            start_resp = await client.post(
                "/api/v1/interview/start",
                json={"candidate_name": "Dave"},
            )
            session_id = start_resp.json()["session_id"]

            end_resp = await client.post(f"/api/v1/interview/{session_id}/end")
        assert end_resp.status_code == 200
        body = end_resp.json()
        assert body["session_id"] == session_id
        assert "skill_summary" in body
        assert "overall_score" in body
        assert "termination_reason" in body

    async def test_end_missing_session_returns_404(self, app_with_mocks):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app_with_mocks), base_url="http://test"
        ) as client:
            resp = await client.post("/api/v1/interview/no-such-session/end")
        assert resp.status_code == 404
