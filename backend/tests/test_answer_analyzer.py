"""
Unit tests for the Answer Analyzer service and API.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.models.answer import EvaluationResult
from app.services.answer_analyzer import analyze_answer


@pytest.fixture
def mock_evaluation_result():
    return EvaluationResult(
        correctness=0.9,
        reasoning_quality=0.8,
        explanation_depth=0.8,
        code_quality=1.0,
        communication_skills=0.9,
        concepts_mastered=["Hash Maps"],
        concepts_failed=["Error Handling"],
        feedback="Good answer overall.",
    )


@pytest.mark.asyncio
@patch("app.services.answer_analyzer.get_llm_client")
async def test_analyze_answer_success(mock_get_llm_client, mock_evaluation_result):
    """Test that analyze_answer formats the prompt and calls the LLM client correctly."""
    mock_client = AsyncMock()
    mock_client.generate_json.return_value = mock_evaluation_result
    mock_get_llm_client.return_value = mock_client

    result = await analyze_answer(
        topic="DSA",
        difficulty=5,
        question_text="How does a hash map work?",
        required_concepts=["Hash function", "Collisions"],
        reference_answer="It uses a hash function to compute an index into an array of buckets.",
        candidate_text="A hash map uses a hash function.",
    )

    assert result == mock_evaluation_result
    mock_client.generate_json.assert_called_once()
    
    # Check that prompt formatting happened
    call_args = mock_client.generate_json.call_args[1]
    assert "How does a hash map work?" in call_args["prompt"]
    assert "A hash map uses a hash function." in call_args["prompt"]


@pytest.mark.asyncio
async def test_submit_answer_api(mock_evaluation_result):
    """Test the POST /api/v1/answers endpoint."""
    from fastapi.testclient import TestClient

    from app.db.postgres import get_db_session
    from app.db.redis_client import get_redis
    from app.main import app
    from app.models.question import Question
    from app.models.session import InterviewSession, QuestionRecord

    # Setup session
    session = InterviewSession(
        candidate_id="user_123",
        topic="DSA",
        difficulty_level=5,
        expires_at="2030-01-01T00:00:00Z",
    )
    record = QuestionRecord(
        question_id="q123",
        question_text="How does a hash map work?",
        topic="DSA",
        difficulty=5,
    )
    session.question_history.append(record)

    # Setup question
    question = Question(
        id="q123",
        title="Hash Maps",
        question="How does a hash map work?",
        topic="DSA",
        difficulty=5,
        concepts=["Hash function"],
        expected_answer="Uses a hash function",
    )

    client = TestClient(app)
    
    mock_redis = AsyncMock()
    mock_redis.ttl.return_value = 3600
    mock_db = AsyncMock()
    
    app.dependency_overrides[get_redis] = lambda: mock_redis
    app.dependency_overrides[get_db_session] = lambda: mock_db

    with patch("app.api.v1.answers.session_service.get_session", new_callable=AsyncMock) as mock_get_session, \
         patch("app.api.v1.answers.get_question", new_callable=AsyncMock) as mock_get_q, \
         patch("app.api.v1.answers.answer_analyzer.analyze_answer", new_callable=AsyncMock) as mock_analyze:
        
        mock_get_session.return_value = session
        mock_get_q.return_value = question
        mock_analyze.return_value = mock_evaluation_result

        response = client.post(
            "/api/v1/answers",
            json={
                "session_id": session.session_id,
                "question_id": "q123",
                "candidate_text": "My answer"
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["evaluation"]["correctness"] == 0.9
        assert data["next_action"] == "continue"

        # Check that redis.set was called to update the session
        mock_redis.set.assert_called_once()
        
        # Check that the modified session had the score set
        updated_session_json = mock_redis.set.call_args[0][1]
        updated_session = InterviewSession.model_validate_json(updated_session_json)
        assert updated_session.question_history[0].score == 0.9
        assert updated_session.question_history[0].feedback == "Good answer overall."
        
    app.dependency_overrides.clear()
