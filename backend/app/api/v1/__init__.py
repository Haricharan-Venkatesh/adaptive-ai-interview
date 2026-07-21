"""
Central router registry.

Every feature router is imported and included here.
The main application only imports THIS file — it never imports individual routers.
"""

from fastapi import APIRouter

from app.api.v1 import answers, auth, dashboard, health, interview, questions, session

# The top-level v1 router — everything is under /api/v1/
api_router = APIRouter(prefix="/api/v1")

# ── Feature routers ───────────────────────────────────────────────────────────
api_router.include_router(health.router)                                    # M1.1
api_router.include_router(session.router)                                   # M1.2
api_router.include_router(questions.router)                                 # M1.3
api_router.include_router(auth.router)                                      # M1.4
api_router.include_router(answers.router)                                   # M2.2
api_router.include_router(interview.interview_router, prefix="/interview")  # M4.3
api_router.include_router(dashboard.router)                                  # Phase 5 M2


