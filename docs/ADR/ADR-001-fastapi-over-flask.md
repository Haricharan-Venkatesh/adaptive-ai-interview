# ADR-001: Use FastAPI Instead of Flask or Django

| Field | Value |
|-------|-------|
| **ID** | ADR-001 |
| **Date** | 2026-07-15 |
| **Status** | Accepted |
| **Implemented In** | Phase 1, Milestone 1.1 |
| **Decided By** | Lead Architect |

---

## Context

We need a Python web framework to build the backend API for the Adaptive AI Interview Assistant.
The backend must handle real-time interview sessions, AI inference calls, async database
operations, and serve a structured REST API consumed by the Next.js frontend.

This is a research-grade system where:
- Developer velocity matters (research deadline)
- API documentation must be auto-generated (reduces maintenance burden)
- Async is critical (LLM calls, DB queries, Redis operations are all I/O-bound)
- Type safety must be enforced throughout

---

## Problem

Which Python web framework should we use as the foundation?

---

## Options Considered

### Option A: Flask
- Micro-framework, minimal opinions
- Synchronous by default (async support added later, incomplete)
- No built-in data validation
- Manual OpenAPI documentation required (flask-smorest, flasgger)
- High flexibility but requires assembling many third-party libraries

### Option B: Django + Django REST Framework
- Full-stack framework, batteries included
- Excellent ORM, admin panel, authentication
- Synchronous-first (Django 3.1+ added async, but DRF is still sync)
- Heavy — ships with features we don't need (templates, sessions, admin)
- OpenAPI generation via `drf-spectacular` (works but verbose)
- Built for CRUD apps, not AI inference pipelines

### Option C: FastAPI ✅
- Modern Python framework built on Starlette + Pydantic
- **Native async/await** — perfect for I/O-bound AI workloads
- **Auto-generates OpenAPI 3.0** docs from type annotations — zero extra work
- **Pydantic v2** integration — type-safe request/response validation at runtime
- **Fastest Python framework** in benchmarks (comparable to Node.js)
- Function-level dependency injection system — clean, testable architecture
- Active community and used in production at Microsoft, Uber, Netflix

---

## Decision

**Use FastAPI.**

---

## Advantages

1. **Async-first** — LLM API calls (Gemini/OpenAI), Redis reads, Neo4j queries all run concurrently
   without blocking. A Flask/DRF synchronous handler would block the thread on every AI call.

2. **Auto-documentation** — The interactive `/docs` (Swagger UI) and `/redoc` pages are
   generated automatically from our Pydantic models. This is essential for a research project
   where other researchers need to understand and test the API.

3. **Type safety at runtime** — Pydantic v2 validates every incoming request body and outgoing
   response. Invalid data raises a 422 error automatically — no manual validation code.

4. **Testability** — FastAPI's `TestClient` lets us test every endpoint without running a server.
   This is why our pytest suite works in CI with zero infrastructure.

5. **Research credibility** — FastAPI is explicitly recommended in the FastAPI paper and widely
   used in ML research backends. Reviewers and readers will recognize it.

---

## Disadvantages

1. **No built-in ORM** — We must choose SQLAlchemy separately (adds configuration overhead).
2. **Smaller ecosystem** than Django — fewer pre-built admin tools, auth plugins.
3. **Learning curve** — Requires understanding async Python, which Flask hides.

---

## Future Implications

- All database operations (M1.3+) must use async drivers: `asyncpg`, `aioredis`, `neo4j` async API.
- The dependency injection system (`Depends()`) should be used consistently for DB sessions,
  auth, and service instantiation — this keeps the code testable and avoids global state.
- When we add WebSocket support for real-time interviews (future), FastAPI handles this natively.
