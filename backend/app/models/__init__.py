"""
Model registry.

Import all models here so that Alembic and SQLAlchemy can discover them
via Base.metadata.
"""

from app.models.base import Base
from app.models.question import Question
from app.models.user import User

__all__ = ["Base", "Question", "User"]
