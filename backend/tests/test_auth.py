from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.postgres import get_db_session
from app.main import app
from app.models.base import Base
from app.models.user import User

# ── Test Database Setup ───────────────────────────────────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)

@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    async with TestingSessionLocal() as session:
        yield session

from httpx import ASGITransport, AsyncClient

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db
    
    # We must use AsyncClient since auth routes use redirect which Starlette TestClient handles synchronously but httpx AsyncClient handles asynchronously
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()



@pytest.mark.asyncio
async def test_github_login_redirect(client: AsyncClient):
    """Test that the login endpoint redirects to GitHub."""
    response = await client.get("/api/v1/auth/login/github", follow_redirects=False)
    assert response.status_code == status.HTTP_302_FOUND
    assert "github.com/login/oauth/authorize" in response.headers["location"]


@pytest.mark.asyncio
async def test_github_callback_success(client: AsyncClient, db_session):
    """Test the GitHub OAuth callback creates a user and issues a JWT."""
    
    mock_token = {"access_token": "mock_gh_token", "token_type": "bearer"}
    mock_user_profile = {
        "id": 1234567,
        "login": "testuser",
        "avatar_url": "https://github.com/avatar.png"
    }
    mock_emails = [
        {"email": "test@example.com", "primary": True, "verified": True}
    ]

    # Mock the authlib OAuth client methods
    with patch("app.api.v1.auth.oauth.github.authorize_access_token", new_callable=AsyncMock) as mock_authorize, \
         patch("app.api.v1.auth.oauth.github.get", new_callable=AsyncMock) as mock_get:
        
        mock_authorize.return_value = mock_token
        
        # mock_get needs to handle two sequential calls: "user" and "user/emails"
        class MockResponse:
            def __init__(self, json_data):
                self._json_data = json_data
            def raise_for_status(self):
                pass
            def json(self):
                return self._json_data

        def mock_get_side_effect(url, **kwargs):
            if url == "user":
                return MockResponse(mock_user_profile)
            elif url == "user/emails":
                return MockResponse(mock_emails)
            return MockResponse({})

        mock_get.side_effect = mock_get_side_effect

        # Call the callback endpoint
        # We need to simulate the request coming back with a code
        response = await client.get("/api/v1/auth/callback/github?code=12345")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify user was saved in DB
        from sqlalchemy.future import select
        stmt = select(User).where(User.github_id == 1234567)
        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()
        
        assert user is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert data["user_id"] == user.id


@pytest.mark.asyncio
async def test_get_current_user_info(client: AsyncClient, db_session):
    """Test getting current user profile with valid JWT."""
    from app.core.security import create_access_token
    from app.models.user import User

    # Create a test user in DB
    user = User(
        github_id=98765,
        email="me@example.com",
        username="me_user",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Generate token
    token = create_access_token(subject=user.id)

    # Request /me endpoint
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["username"] == "me_user"
    assert data["github_id"] == 98765


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    """Test /me endpoint without token returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test /me endpoint with invalid token returns 401."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
