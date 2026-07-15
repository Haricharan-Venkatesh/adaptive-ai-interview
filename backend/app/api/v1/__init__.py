"""
Central router registry.

Every feature router is imported and included here.
The main application only imports THIS file — it never imports individual routers.

This pattern is called the "Router Registry" pattern and keeps main.py clean.
When you add a new feature (e.g., interview.py), you only change this file.
"""

from fastapi import APIRouter

from app.api.v1 import health

# The top-level v1 router — everything is under /api/v1/
api_router = APIRouter(prefix="/api/v1")

# ── Feature routers ───────────────────────────────────────────────────────────
api_router.include_router(health.router)

# Future milestones will register routers here:
# from app.api.v1 import interview, questions, answers, reports, auth
# api_router.include_router(interview.router)
# api_router.include_router(questions.router)
# api_router.include_router(answers.router)
# api_router.include_router(reports.router)
# api_router.include_router(auth.router)
