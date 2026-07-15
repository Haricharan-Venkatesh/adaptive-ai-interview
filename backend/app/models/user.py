from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# ─── SQLAlchemy ORM Model ─────────────────────────────────────────────────────
class User(Base):
    """
    SQLAlchemy model for User.
    Users authenticate via GitHub OAuth.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    github_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


# ─── Pydantic Schemas ────────────────────────────────────────────────────────
class UserBase(BaseModel):
    """Base fields for User."""
    email: EmailStr
    username: str
    avatar_url: str | None = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    """Payload for creating a new user (from GitHub OAuth)."""
    github_id: int


class UserUpdate(BaseModel):
    """Payload for updating an existing user."""
    email: EmailStr | None = None
    username: str | None = None
    avatar_url: str | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    """Response schema for User."""
    id: int
    github_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
