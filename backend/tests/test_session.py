"""
Test suite for Phase 1, Milestone 1.2 — Redis Session Management.

Strategy:
  - Uses fakeredis.aioredis.FakeRedis as an in-memory Redis substitute.
    No real Redis process needed — tests run in pure Python.
  - FastAPI's dependency_overrides replaces get_redis with a fake implementation.
  - Each test class gets a fresh fakeredis instance to ensure test isolation.
  - The session fixture creates a valid session before each test that needs one.

Run with:
  pytest tests/test_session.py -v
"""

import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient

from app.db.redis_client import get_redis
from app.main import app  # noqa: E402

# ── Shared fake Redis factory ─────────────────────────────────────────────────

def make_fake_redis() -> fakeredis.aioredis.FakeRedis:
    """Create a fresh in-memory FakeRedis instance."""
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


def make_client(fake_redis: fakeredis.aioredis.FakeRedis) -> TestClient:
    """
    Build a TestClient with the get_redis dependency overridden.

    The override is an async generator that yields the fake client —
    exactly mirroring the real get_redis() signature.
    """
    async def override_get_redis():  # noqa: RUF029
        yield fake_redis

    app.dependency_overrides[get_redis] = override_get_redis
    client = TestClient(app)
    return client


# ── Create session helpers ────────────────────────────────────────────────────

CREATE_PAYLOAD = {
    "candidate_id": "test_candidate_001",
    "topic": "DSA",
    "difficulty_level": 5,
}


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/sessions
# ═══════════════════════════════════════════════════════════════════════════════

class TestCreateSession:
    """Tests for POST /api/v1/sessions."""

    def setup_method(self):
        self.fake_redis = make_fake_redis()
        self.client = make_client(self.fake_redis)

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_create_returns_201(self):
        response = self.client.post("/api/v1/sessions", json=CREATE_PAYLOAD)
        assert response.status_code == 201

    def test_create_returns_session_id(self):
        response = self.client.post("/api/v1/sessions", json=CREATE_PAYLOAD)
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) == 36  # UUID4 format

    def test_create_stores_candidate_id(self):
        response = self.client.post("/api/v1/sessions", json=CREATE_PAYLOAD)
        assert response.json()["candidate_id"] == "test_candidate_001"

    def test_create_stores_topic(self):
        response = self.client.post("/api/v1/sessions", json=CREATE_PAYLOAD)
        assert response.json()["topic"] == "DSA"

    def test_create_stores_difficulty(self):
        response = self.client.post("/api/v1/sessions", json=CREATE_PAYLOAD)
        assert response.json()["difficulty_level"] == 5

    def test_create_default_status_is_active(self):
        response = self.client.post("/api/v1/sessions", json=CREATE_PAYLOAD)
        assert response.json()["status"] == "active"

    def test_create_empty_question_history(self):
        response = self.client.post("/api/v1/sessions", json=CREATE_PAYLOAD)
        assert response.json()["question_history"] == []

    def test_create_zero_questions_asked(self):
        response = self.client.post("/api/v1/sessions", json=CREATE_PAYLOAD)
        assert response.json()["total_questions_asked"] == 0

    def test_create_has_expires_at(self):
        response = self.client.post("/api/v1/sessions", json=CREATE_PAYLOAD)
        assert "expires_at" in response.json()

    def test_create_with_metadata(self):
        payload = {**CREATE_PAYLOAD, "metadata": {"recruiter": "Alice", "round": 2}}
        response = self.client.post("/api/v1/sessions", json=payload)
        assert response.json()["metadata"]["recruiter"] == "Alice"

    def test_create_missing_candidate_id_returns_422(self):
        response = self.client.post("/api/v1/sessions", json={"topic": "DSA"})
        assert response.status_code == 422

    def test_create_invalid_difficulty_returns_422(self):
        response = self.client.post(
            "/api/v1/sessions",
            json={**CREATE_PAYLOAD, "difficulty_level": 99},
        )
        assert response.status_code == 422

    def test_create_invalid_topic_returns_422(self):
        response = self.client.post(
            "/api/v1/sessions",
            json={**CREATE_PAYLOAD, "topic": "NotAValidTopic"},
        )
        assert response.status_code == 422

    def test_two_sessions_have_different_ids(self):
        id1 = self.client.post("/api/v1/sessions", json=CREATE_PAYLOAD).json()["session_id"]
        id2 = self.client.post("/api/v1/sessions", json=CREATE_PAYLOAD).json()["session_id"]
        assert id1 != id2


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/sessions/{session_id}
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetSession:
    """Tests for GET /api/v1/sessions/{session_id}."""

    def setup_method(self):
        self.fake_redis = make_fake_redis()
        self.client = make_client(self.fake_redis)
        # Create one session to retrieve
        resp = self.client.post("/api/v1/sessions", json=CREATE_PAYLOAD)
        self.session_id = resp.json()["session_id"]

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_get_existing_session_returns_200(self):
        response = self.client.get(f"/api/v1/sessions/{self.session_id}")
        assert response.status_code == 200

    def test_get_returns_correct_session_id(self):
        response = self.client.get(f"/api/v1/sessions/{self.session_id}")
        assert response.json()["session_id"] == self.session_id

    def test_get_nonexistent_session_returns_404(self):
        response = self.client.get("/api/v1/sessions/nonexistent-id")
        assert response.status_code == 404

    def test_get_404_contains_detail(self):
        response = self.client.get("/api/v1/sessions/ghost")
        assert "not found" in response.json()["detail"].lower()


# ═══════════════════════════════════════════════════════════════════════════════
# PATCH /api/v1/sessions/{session_id}
# ═══════════════════════════════════════════════════════════════════════════════

class TestUpdateSession:
    """Tests for PATCH /api/v1/sessions/{session_id}."""

    def setup_method(self):
        self.fake_redis = make_fake_redis()
        self.client = make_client(self.fake_redis)
        resp = self.client.post("/api/v1/sessions", json=CREATE_PAYLOAD)
        self.session_id = resp.json()["session_id"]

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_update_status_to_completed(self):
        response = self.client.patch(
            f"/api/v1/sessions/{self.session_id}",
            json={"status": "completed"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_update_difficulty_level(self):
        response = self.client.patch(
            f"/api/v1/sessions/{self.session_id}",
            json={"difficulty_level": 8},
        )
        assert response.json()["difficulty_level"] == 8

    def test_update_competency_scores(self):
        response = self.client.patch(
            f"/api/v1/sessions/{self.session_id}",
            json={"competency_scores": {"Recursion": 0.9, "DFS": 0.7}},
        )
        scores = response.json()["competency_scores"]
        assert scores["Recursion"] == pytest.approx(0.9)
        assert scores["DFS"] == pytest.approx(0.7)

    def test_update_partial_leaves_other_fields_intact(self):
        # Update only status
        self.client.patch(
            f"/api/v1/sessions/{self.session_id}",
            json={"status": "paused"},
        )
        # Verify candidate_id unchanged
        get_resp = self.client.get(f"/api/v1/sessions/{self.session_id}")
        assert get_resp.json()["candidate_id"] == "test_candidate_001"
        assert get_resp.json()["status"] == "paused"

    def test_update_nonexistent_session_returns_404(self):
        response = self.client.patch(
            "/api/v1/sessions/ghost-id",
            json={"status": "completed"},
        )
        assert response.status_code == 404

    def test_update_invalid_status_returns_422(self):
        response = self.client.patch(
            f"/api/v1/sessions/{self.session_id}",
            json={"status": "invalid_status"},
        )
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# DELETE /api/v1/sessions/{session_id}
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeleteSession:
    """Tests for DELETE /api/v1/sessions/{session_id}."""

    def setup_method(self):
        self.fake_redis = make_fake_redis()
        self.client = make_client(self.fake_redis)
        resp = self.client.post("/api/v1/sessions", json=CREATE_PAYLOAD)
        self.session_id = resp.json()["session_id"]

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_delete_existing_session_returns_204(self):
        response = self.client.delete(f"/api/v1/sessions/{self.session_id}")
        assert response.status_code == 204

    def test_deleted_session_not_found_on_get(self):
        self.client.delete(f"/api/v1/sessions/{self.session_id}")
        response = self.client.get(f"/api/v1/sessions/{self.session_id}")
        assert response.status_code == 404

    def test_delete_nonexistent_returns_404(self):
        response = self.client.delete("/api/v1/sessions/ghost-id")
        assert response.status_code == 404

    def test_double_delete_returns_404(self):
        self.client.delete(f"/api/v1/sessions/{self.session_id}")
        response = self.client.delete(f"/api/v1/sessions/{self.session_id}")
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/sessions/{session_id}/questions
# ═══════════════════════════════════════════════════════════════════════════════

class TestAppendQuestion:
    """Tests for POST /api/v1/sessions/{session_id}/questions."""

    QUESTION_PAYLOAD = {
        "question_text": "Explain BFS vs DFS.",
        "topic": "Graph Traversal",
        "difficulty": 4,
    }

    def setup_method(self):
        self.fake_redis = make_fake_redis()
        self.client = make_client(self.fake_redis)
        resp = self.client.post("/api/v1/sessions", json=CREATE_PAYLOAD)
        self.session_id = resp.json()["session_id"]

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_append_question_returns_200(self):
        response = self.client.post(
            f"/api/v1/sessions/{self.session_id}/questions",
            json=self.QUESTION_PAYLOAD,
        )
        assert response.status_code == 200

    def test_append_increments_total_questions(self):
        self.client.post(
            f"/api/v1/sessions/{self.session_id}/questions",
            json=self.QUESTION_PAYLOAD,
        )
        session = self.client.get(f"/api/v1/sessions/{self.session_id}").json()
        assert session["total_questions_asked"] == 1

    def test_append_adds_to_history(self):
        self.client.post(
            f"/api/v1/sessions/{self.session_id}/questions",
            json=self.QUESTION_PAYLOAD,
        )
        session = self.client.get(f"/api/v1/sessions/{self.session_id}").json()
        assert len(session["question_history"]) == 1
        assert session["question_history"][0]["question_text"] == "Explain BFS vs DFS."

    def test_append_multiple_questions(self):
        for _ in range(3):
            self.client.post(
                f"/api/v1/sessions/{self.session_id}/questions",
                json=self.QUESTION_PAYLOAD,
            )
        session = self.client.get(f"/api/v1/sessions/{self.session_id}").json()
        assert session["total_questions_asked"] == 3
        assert len(session["question_history"]) == 3

    def test_append_with_score_and_feedback(self):
        payload = {
            **self.QUESTION_PAYLOAD,
            "answer_text": "BFS uses a queue...",
            "score": 0.85,
            "feedback": "Good explanation.",
        }
        self.client.post(
            f"/api/v1/sessions/{self.session_id}/questions", json=payload
        )
        record = self.client.get(
            f"/api/v1/sessions/{self.session_id}"
        ).json()["question_history"][0]
        assert record["score"] == pytest.approx(0.85)
        assert record["feedback"] == "Good explanation."

    def test_append_question_has_unique_id(self):
        self.client.post(
            f"/api/v1/sessions/{self.session_id}/questions",
            json=self.QUESTION_PAYLOAD,
        )
        self.client.post(
            f"/api/v1/sessions/{self.session_id}/questions",
            json=self.QUESTION_PAYLOAD,
        )
        history = self.client.get(
            f"/api/v1/sessions/{self.session_id}"
        ).json()["question_history"]
        assert history[0]["question_id"] != history[1]["question_id"]

    def test_append_to_nonexistent_session_returns_404(self):
        response = self.client.post(
            "/api/v1/sessions/ghost-id/questions",
            json=self.QUESTION_PAYLOAD,
        )
        assert response.status_code == 404

    def test_append_missing_required_field_returns_422(self):
        # Missing topic
        response = self.client.post(
            f"/api/v1/sessions/{self.session_id}/questions",
            json={"question_text": "What is BFS?", "difficulty": 3},
        )
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# Existing health tests backward-compatibility check
# ═══════════════════════════════════════════════════════════════════════════════

class TestHealthWithRedisNotInitialized:
    """
    Verify that health endpoints remain backward-compatible
    when no Redis pool is initialized (unit test environment).
    """

    def setup_method(self):
        # No override — uses real app without Redis pool
        self.client = TestClient(app)

    def test_health_still_returns_200(self):
        response = self.client.get("/api/v1/health")
        assert response.status_code == 200

    def test_readiness_still_returns_200(self):
        # Redis not initialized → only "api" in services → ready=True
        response = self.client.get("/api/v1/health/ready")
        assert response.status_code == 200

    def test_readiness_ready_true_without_redis(self):
        data = self.client.get("/api/v1/health/ready").json()
        assert data["ready"] is True

    def test_readiness_has_api_service(self):
        data = self.client.get("/api/v1/health/ready").json()
        assert "api" in data["services"]
