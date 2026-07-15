from datetime import UTC, datetime
from typing import Any

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token
from app.db.postgres import get_db_session
from app.models.user import User, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

# ─── Authlib OAuth Setup ──────────────────────────────────────────────────────
oauth = OAuth()
oauth.register(
    name="github",
    client_id=settings.github_client_id,
    client_secret=settings.github_client_secret,
    access_token_url="https://github.com/login/oauth/access_token",
    access_token_params=None,
    authorize_url="https://github.com/login/oauth/authorize",
    authorize_params=None,
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)


# ─── Dependencies ─────────────────────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Dependency to retrieve the current user from JWT token."""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    return user


# ─── Endpoints ────────────────────────────────────────────────────────────────
@router.get("/login/github")
async def github_login(request: Request) -> Any:
    """Redirect to GitHub for OAuth login."""
    redirect_uri = str(request.url_for("github_callback"))
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/callback/github")
async def github_callback(request: Request, db: AsyncSession = Depends(get_db_session)) -> Any:
    """Handle GitHub OAuth callback, create/update user, and issue JWT."""
    try:
        token = await oauth.github.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authorization failed: {str(e)}"
        )

    # Fetch user data from GitHub API
    resp = await oauth.github.get("user", token=token)
    resp.raise_for_status()
    github_user = resp.json()
    
    # Fetch user emails
    email_resp = await oauth.github.get("user/emails", token=token)
    email_resp.raise_for_status()
    emails = email_resp.json()
    
    primary_email = next((e["email"] for e in emails if e["primary"]), None)
    if not primary_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No primary email found on GitHub account"
        )

    # Upsert user in database
    github_id = github_user["id"]
    stmt = select(User).where(User.github_id == github_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            github_id=github_id,
            email=primary_email,
            username=github_user["login"],
            avatar_url=github_user.get("avatar_url"),
        )
        db.add(user)
    else:
        user.email = primary_email
        user.username = github_user["login"]
        user.avatar_url = github_user.get("avatar_url")
        user.updated_at = datetime.now(UTC)
        
    await db.commit()
    await db.refresh(user)

    # Issue JWT token
    access_token = create_access_token(subject=user.id)
    
    # In a real app, redirect to frontend with token in cookie or URL hash
    # e.g., return RedirectResponse(url=f"{settings.frontend_url}/login?token={access_token}")
    # For API response, we'll return JSON directly if not a browser redirect:
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> Any:
    """Get the currently logged-in user profile."""
    return current_user
