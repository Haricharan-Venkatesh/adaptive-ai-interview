"""
Tests for Questions CRUD and Question Engine.

Uses an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`) to 
ensure tests are fast and isolated, avoiding the need for a real Postgres instance.
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.postgres import get_db_session
from app.main import app
from app.models.base import Base
from app.models.question import Question
from scripts.seed_questions import seed

# ── Test Database Setup ───────────────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)

@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_test_db():
    """Create all tables in the in-memory SQLite DB before each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup not strictly needed for :memory: but good practice
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    """Provide an async session for database operations."""
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> TestClient:
    """Provide a TestClient with the database dependency overridden."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ── Fixtures ──────────────────────────────────────────────────────────────────

VALID_QUESTION_PAYLOAD = {
    "title": "Reverse a Linked List",
    "question": "Write a function to reverse a singly linked list.",
    "topic": "DSA",
    "difficulty": 3,
    "concepts": ["Linked List", "Pointers"],
    "tags": ["dsa", "easy"],
    "expected_answer": "Iterate while maintaining prev and next pointers.",
    "sample_code": "def reverse(head):\n  ...",
    "language": "python",
    "hints": ["Use three pointers: prev, curr, next"]
}

@pytest_asyncio.fixture
async def sample_question(db_session: AsyncSession) -> Question:
    question = Question(**VALID_QUESTION_PAYLOAD)
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)
    return question


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_question(client: TestClient):
    response = client.post("/api/v1/questions", json=VALID_QUESTION_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == VALID_QUESTION_PAYLOAD["title"]
    assert data["topic"] == "DSA"
    assert "id" in data
    assert "created_at" in data

@pytest.mark.asyncio
async def test_get_question(client: TestClient, sample_question: Question):
    response = client.get(f"/api/v1/questions/{sample_question.id}")
    assert response.status_code == 200
    assert response.json()["title"] == sample_question.title

@pytest.mark.asyncio
async def test_get_question_not_found(client: TestClient):
    response = client.get("/api/v1/questions/nonexistent-id")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_question(client: TestClient, sample_question: Question):
    response = client.patch(
        f"/api/v1/questions/{sample_question.id}",
        json={"difficulty": 8, "topic": "Advanced DSA"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["difficulty"] == 8
    assert data["topic"] == "Advanced DSA"
    assert data["title"] == sample_question.title  # Unchanged

@pytest.mark.asyncio
async def test_delete_question(client: TestClient, sample_question: Question, db_session: AsyncSession):
    response = client.delete(f"/api/v1/questions/{sample_question.id}")
    assert response.status_code == 204
    
    # Verify it's gone
    resp = client.get(f"/api/v1/questions/{sample_question.id}")
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_list_questions(client: TestClient, sample_question: Question):
    # Add a second question
    payload2 = {**VALID_QUESTION_PAYLOAD, "title": "Detect Cycle"}
    client.post("/api/v1/questions", json=payload2)
    
    response = client.get("/api/v1/questions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

@pytest.mark.asyncio
async def test_search_questions_by_topic(client: TestClient, sample_question: Question):
    # Add a System Design question
    payload2 = {**VALID_QUESTION_PAYLOAD, "topic": "System Design", "title": "URL Shortener"}
    client.post("/api/v1/questions", json=payload2)
    
    response = client.get("/api/v1/questions/search?topic=System Design")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "URL Shortener"

@pytest.mark.asyncio
async def test_search_questions_by_difficulty(client: TestClient, sample_question: Question):
    payload2 = {**VALID_QUESTION_PAYLOAD, "difficulty": 8, "title": "Hard Graph"}
    client.post("/api/v1/questions", json=payload2)
    
    response = client.get("/api/v1/questions/search?difficulty_min=7")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Hard Graph"

@pytest.mark.asyncio
async def test_health_ready_without_postgres(client: TestClient):
    """
    Readiness probe test.

    In CI/test environments where the real Postgres engine is initialised
    (because the lifespan hook ran), postgres WILL appear in the services dict.
    In environments where only the SQLite override is active and init_db()
    was never called, postgres is omitted.  Both outcomes are valid.
    """
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
    assert "api" in data["services"]
    # postgres may or may not appear depending on whether the real engine was
    # initialised in this test run — both are acceptable outcomes.
    if "postgres" in data["services"]:
        assert data["services"]["postgres"]["status"] in ("ok", "unhealthy", "unknown")

@pytest.mark.asyncio
async def test_seed_questions(db_session: AsyncSession):
    import app.db.postgres as pg
    
    # Temporarily override the session factory in postgres.py for the seed script
    original_factory = pg._session_factory
    original_init = pg.init_db
    original_close = pg.close_db
    
    # Mock init and close so they don't overwrite our test factory
    async def mock_init():
        pass
    async def mock_close():
        pass
        
    pg._session_factory = TestingSessionLocal
    pg.init_db = mock_init
    pg.close_db = mock_close
    
    try:
        # Run the seed script
        await seed()
        
        # Check that questions were loaded
        from sqlalchemy import func
        from sqlalchemy.future import select
        
        stmt = select(func.count(Question.id))
        result = await db_session.execute(stmt)
        count = result.scalar()
        
        assert count > 0
        
        # Run again to test duplicate handling
        await seed()
        
        result2 = await db_session.execute(stmt)
        count2 = result2.scalar()
        
        assert count == count2
    finally:
        # Restore original objects
        pg._session_factory = original_factory
        pg.init_db = original_init
        pg.close_db = original_close
