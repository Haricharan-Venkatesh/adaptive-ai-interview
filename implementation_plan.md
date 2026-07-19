# Adaptive AI Interview Assistant — Implementation Plan

> **Status**: Phase 3, M3.1 ✅ Complete. Next Milestone: Phase 3, M3.2 BKT Baseline.
> **Research Target**: IEEE/ACM-quality paper + production-grade portfolio project.

---

## Architecture Analysis

### Image 1: System Architecture Pipeline

A **closed-loop adaptive pipeline** with 6 core modules:

| Module | Name | Function |
|--------|------|----------|
| 2.1 | Interview Question Engine | Initial question selection + filtering |
| 2.2 | Multimodal Answer Understanding | Text/code analysis → Unified Answer Representation |
| 2.3 | Dynamic Competency Modeling | Skill graph + knowledge state update |
| 2.4 | Adaptive Question Selection | Gap analysis → optimal next question |
| 2.5 | Current Confidence Gate | Decision: "Enough" vs "Not Enough" |
| 2.6 | Next Question Generation | Retrieval (RAG) + LLM fallback |

## Phase 1 Milestone 1.3: Question Database & Seed Data

### Architecture Integration
M1.3 introduces PostgreSQL as the primary persistent data store using `SQLAlchemy 2.x` with an `asyncpg` driver and `Alembic` for migrations.
- **Data Layer:** `app/db/postgres.py` will provide the async engine and session factory, paralleling the structure of `app/db/redis_client.py`.
- **Domain Layer:** `app/models/question.py` will define both the SQLAlchemy ORM model (for persistence) and Pydantic schemas (for API validation/serialization), maintaining separation of concerns.
- **Service Layer:** `app/services/question_engine.py` will contain pure async functions for retrieving and filtering questions, injecting the DB session via FastAPI `Depends`, which makes testing easy.
- **API Layer:** `app/api/v1/questions.py` exposes the REST endpoints, integrating seamlessly into the existing `api_router`.
- **Health Probes:** The existing readiness probe (`app/api/v1/health.py`) will be extended to verify PostgreSQL connectivity via a simple `SELECT 1` ping.
- **Seeding:** A dedicated JSON dataset and script will seed the database without interfering with runtime API operations.

### Files to Create / Modify

#### [MODIFY] [pyproject.toml](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/pyproject.toml)
Add `sqlalchemy`, `asyncpg`, `alembic` to dependencies.

#### [MODIFY] [.env](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/.env) / [.env.example](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/.env.example)
Add `DATABASE_URL` (PostgreSQL connection string).

#### [MODIFY] [config.py](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/app/core/config.py)
Add `database_url` configuration.

#### [NEW] [postgres.py](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/app/db/postgres.py)
Async SQLAlchemy engine, session maker, dependency injection, and health check.

#### [NEW] [question.py](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/app/models/question.py)
SQLAlchemy ORM model and Pydantic schemas for Question records.

#### [NEW] [alembic.ini](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/alembic.ini) / [env.py](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/alembic/env.py) / [versions/...](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/alembic/versions/)
Alembic migration configuration and initial migration script.

#### [NEW] [seed_questions.json](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/data/questions/seed_questions.json)
Dataset of 50+ interview questions.

#### [NEW] [seed_questions.py](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/scripts/seed_questions.py)
Script to parse JSON and insert questions into PostgreSQL.

#### [NEW] [question_engine.py](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/app/services/question_engine.py)
Service logic for CRUD and filtering questions.

#### [NEW] [questions.py](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/app/api/v1/questions.py)
FastAPI router for question endpoints.

#### [MODIFY] [\_\_init\_\_.py (router)](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/app/api/v1/__init__.py)
Register the new `/questions` router.

#### [MODIFY] [health.py](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/app/api/v1/health.py)
Extend readiness probe to include PostgreSQL.

#### [MODIFY] [main.py](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/app/main.py)
Add DB connection initialization/closing to lifespan.

#### [NEW] [test_questions.py](file:///C:/Users/HARICHARAN%20VENKATESH/.gemini/antigravity/scratch/adaptive-ai-interview/backend/tests/test_questions.py)
Test cases for question CRUD, filtering, pagination, and seed loading.

**Output Layer** — Comprehensive Candidate Report (competency graph, strengths, weaknesses, learning recommendations)

### Image 2: Implementation Pathway

| Step | Implementation | Technologies |
|------|---------------|-------------|
| 1 | Foundation: API, Question DB, Chat UI | FastAPI, Redis, PostgreSQL |
| 2 | Answer Processing: LLM evaluation, metrics | Gemini/OpenAI, Embeddings |
| 3 | Dynamic Modeling: Skill graph, knowledge state | NetworkX, BKT, DKT, GNN |
| 4 | Adaptive Selection: Skill gaps, RAG, routing | Graph-RAG, Neo4j, ChromaDB |
| 5 | Feedback & Output: Termination, report | LLM summarization, PDF/Markdown |

---

## Complete Repository Structure

```
adaptive-ai-interview/
│
├── backend/                                    # FastAPI Python Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                             # ✅ M1.1 — App factory, lifespan, middleware
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py                 # ✅ M1.1 — Router registry
│   │   │       ├── health.py                   # ✅ M1.1 — Liveness + readiness probes
│   │   │       ├── session.py                  # M1.2 — Redis interview session endpoints
│   │   │       ├── questions.py                # M1.3 — Question CRUD + search
│   │   │       ├── auth.py                     # M1.4 — GitHub OAuth callback
│   │   │       ├── interview.py                # M2.x — Interview session flow
│   │   │       ├── answers.py                  # M2.2 — Answer submission + evaluation
│   │   │       └── reports.py                  # M5.1 — Report generation
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py                       # ✅ M1.1 — Pydantic v2 settings
│   │   │   ├── logging.py                      # ✅ M1.1 — structlog (JSON/console)
│   │   │   └── security.py                     # M1.4 — JWT + OAuth helpers
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── redis_client.py                 # M1.2 — Async Redis pool + helpers
│   │   │   ├── postgres.py                     # M1.3 — Async SQLAlchemy engine
│   │   │   └── neo4j_client.py                 # M3.3 — Async Neo4j driver + Cypher helpers
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── health.py                       # ✅ M1.1 — HealthResponse, ReadinessResponse
│   │   │   ├── session.py                      # M1.2 — InterviewSession Pydantic model
│   │   │   ├── question.py                     # M1.3 — Question ORM + schemas
│   │   │   ├── answer.py                       # M2.2 — EvaluationResult model
│   │   │   ├── candidate.py                    # M3.x — CompetencyNode, SkillEdge
│   │   │   └── report.py                       # M5.1 — InterviewReport model
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── session_service.py              # M1.2 — Session CRUD (Redis)
│   │   │   ├── question_engine.py              # M1.3 — Retrieval + filtering
│   │   │   ├── answer_analyzer.py              # M2.2 — LLM-based evaluation
│   │   │   ├── ast_analyzer.py                 # M2.3 — Python AST code analysis
│   │   │   ├── skill_graph.py                  # M3.1 — NetworkX competency graph
│   │   │   ├── knowledge_tracer.py             # M3.2/M3.6 — KnowledgeTracerFactory
│   │   │   ├── adaptive_selector.py            # M4.3 — Adaptive question selection
│   │   │   └── report_generator.py             # M5.1 — Report generation pipeline
│   │   └── ai/
│   │       ├── __init__.py
│   │       ├── llm_client.py                   # M2.1 — Gemini/OpenAI unified wrapper
│   │       ├── prompts/
│   │       │   ├── __init__.py
│   │       │   ├── answer_eval.py              # M2.1 — Answer evaluation prompt
│   │       │   ├── question_gen.py             # M4.2 — Question generation prompt
│   │       │   └── report_gen.py               # M5.1 — Report generation prompt
│   │       ├── embeddings.py                   # M4.1 — Text embedding service
│   │       └── rag_engine.py                   # M4.2 — Graph-RAG pipeline
│   ├── ai_models/
│   │   ├── knowledge_tracing/
│   │   │   ├── bkt.py                          # M3.2 — Bayesian Knowledge Tracing
│   │   │   ├── dkt.py                          # M3.4 — Deep Knowledge Tracing (LSTM)
│   │   │   ├── factory.py                      # M3.6 — KnowledgeTracerFactory
│   │   │   └── checkpoints/                    # Saved PyTorch model weights (.pt)
│   │   └── graph_neural_net/
│   │       ├── gat_model.py                    # M3.5 — Graph Attention Network
│   │       ├── train.py                        # M3.5 — Training script
│   │       └── checkpoints/                    # Saved GNN weights (.pt)
│   ├── data/
│   │   └── questions/
│   │       └── seed_questions.json             # M1.3 — 50+ interview questions
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_health.py                      # ✅ M1.1 — 14/14 passing
│   │   ├── test_session.py                     # M1.2
│   │   ├── test_questions.py                   # M1.3
│   │   ├── test_answer_analyzer.py             # M2.2
│   │   ├── test_bkt.py                         # M3.2
│   │   ├── test_dkt.py                         # M3.4
│   │   └── test_gnn.py                         # M3.5
│   ├── pyproject.toml                          # ✅ M1.1 — hatch, ruff, pytest
│   ├── .env                                    # ✅ M1.1 — Dev secrets (gitignored)
│   ├── .env.example                            # ✅ M1.1 — Documentation template
│   ├── .gitignore                              # ✅ M1.1
│   └── Dockerfile                              # M6.2
│
├── frontend/                                   # Next.js 15 + TypeScript
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx                        # M1.5 — Landing page
│   │   │   ├── interview/page.tsx              # M1.5 — Chat interview UI
│   │   │   └── dashboard/page.tsx              # M5.2 — Recruiter dashboard
│   │   ├── components/
│   │   │   ├── chat/                           # M1.5 — Chat interface
│   │   │   ├── editor/                         # M1.5 — Monaco code editor
│   │   │   ├── graph/                          # M5.3 — D3/Cytoscape skill graph
│   │   │   └── dashboard/                      # M5.2 — Analytics widgets
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── types.ts
│   │   └── styles/globals.css
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── Dockerfile                              # M6.2
│
├── research/                                   # ← NEW
│   ├── papers/                                 # Reference papers index
│   ├── experiments/                            # BKT vs DKT vs GNN results
│   ├── benchmarks/                             # Evaluation scripts
│   └── datasets/                               # Public KT datasets (ASSISTments)
│
├── notebooks/                                  # ← NEW — Jupyter exploration
│   ├── 01_data_exploration/
│   ├── 02_bkt_prototype/
│   ├── 03_dkt_prototype/
│   ├── 04_gnn_prototype/
│   ├── 05_rag_experiments/
│   └── 06_report_analysis/
│
├── docs/
│   ├── ADR/                                    # ← NEW — Architecture Decision Records
│   │   ├── README.md                           # ADR index
│   │   ├── ADR-001-fastapi-over-flask.md       # ✅ Written
│   │   ├── ADR-002-redis-for-sessions.md       # ✅ Written
│   │   ├── ADR-003-neo4j-for-graph.md          # ✅ Written
│   │   ├── ADR-004-graph-rag-over-vector-rag.md # ✅ Written
│   │   ├── ADR-005-pytorch-over-tensorflow.md  # ✅ Written
│   │   ├── ADR-006-dkt-over-bkt.md             # ✅ Written
│   │   └── ADR-007-gnn-for-competency.md       # ✅ Written
│   └── architecture.md
│
├── docker-compose.yml                          # M6.2
├── .github/
│   └── workflows/ci.yml                        # M6.3
├── .gitignore                                  # ✅ M1.1
└── README.md

```

---

## Development Roadmap

### Phase 1 — Foundation

| Milestone | Name | Status | ADR |
|-----------|------|--------|-----|
| M1.1 | FastAPI Foundation — health, config, logging, tests | ✅ **COMPLETE** (commit c06068a) | ADR-001 |
| M1.2 | Redis Session Management | ✅ **COMPLETE** (commit f8df7a0) | ADR-002 |
| M1.3 | Question Database & Seed Data | ✅ **COMPLETE** (commit 467420a) | — |
| M1.4 | GitHub OAuth Authentication | ✅ **COMPLETE** (commit 9ec0fce) | — |
| M1.5 | Next.js Frontend + Chat UI | ✅ **COMPLETE** (commit b19b240) | — |

### Phase 2 — Answer Processing

| Milestone | Name | Status |
|-----------|------|--------|
| M2.1 | LLM Integration (Gemini / OpenAI) | ✅ **COMPLETE** |
| M2.2 | Answer Processing Pipeline | 🔲 **Next** |
| M2.3 | AST-based Code Analysis | 🔲 |

### Phase 3 — Dynamic Modeling ← EXPANDED

| Milestone | Name | Status | ADR |
|-----------|------|--------|-----|
| M3.1 | NetworkX In-Memory Skill Graph | ✅ **COMPLETE** | — |
| M3.2 | **BKT Baseline** (Bayesian Knowledge Tracing) | 🔲 | ADR-006 |
| M3.3 | Neo4j Graph Persistence | 🔲 | ADR-003 |
| M3.4 | **Deep Knowledge Tracing** (PyTorch LSTM) | 🔲 | ADR-005, ADR-006 |
| M3.5 | **Graph Neural Network** (PyTorch Geometric GAT) | 🔲 | ADR-005, ADR-007 |
| M3.6 | **Production Swap**: Replace BKT with DKT+GNN via KnowledgeTracerFactory | 🔲 | ADR-006, ADR-007 |

> **Why this order?**
> M3.2 (BKT) provides an immediately working knowledge tracer.
> M3.4 (DKT) adds the neural model. M3.5 (GNN) adds graph propagation.
> M3.6 integrates them with a factory pattern and produces the BKT vs DKT comparison data for the paper.

### Phase 4 — Adaptive Question Selection

| Milestone | Name | Status | ADR |
|-----------|------|--------|-----|
| M4.1 | Vector Embeddings (sentence-transformers + ChromaDB) | 🔲 | — |
| M4.2 | Graph-RAG Retrieval | 🔲 | ADR-004 |
| M4.3 | Adaptive Question Selection Engine (full pipeline) | 🔲 | — |

### Phase 5 — Output Layer

| Milestone | Name | Status |
|-----------|------|--------|
| M5.1 | Report Generation Pipeline | 🔲 |
| M5.2 | Recruiter Dashboard | 🔲 |
| M5.3 | Graph Visualization (D3.js / Cytoscape.js) | 🔲 |

### Phase 6 — Production

| Milestone | Name | Status |
|-----------|------|--------|
| M6.1 | Full Testing Suite (≥80% coverage) | 🔲 |
| M6.2 | Docker + docker-compose | 🔲 |
| M6.3 | CI/CD (GitHub Actions) | 🔲 |
| M6.4 | Performance Evaluation | 🔲 |
| M6.5 | Research Paper Draft | 🔲 |

---

## Architecture → Implementation Mapping

| Architecture Module | Milestones |
|---------------------|-----------|
| 2.1 Interview Question Engine | M1.3 (DB), M4.3 (Adaptive) |
| 2.2 Multimodal Answer Understanding | M2.1 (LLM), M2.2 (Pipeline), M2.3 (AST) |
| 2.3 Dynamic Competency Modeling | M3.1 (Graph), M3.2 (BKT), M3.4 (DKT), M3.5 (GNN), M3.6 (Factory) |
| 2.4 Adaptive Question Selection | M4.1 (Embeddings), M4.2 (RAG), M4.3 (Engine) |
| 2.5 Confidence Gate | M4.3 (integrated) |
| 2.6 Next Question Generation | M4.2 (RAG), M4.3 (LLM fallback) |
| 3. Output Layer | M5.1, M5.2, M5.3 |
| Infrastructure | M1.1–M1.5, M6.1–M6.5 |

---

## Knowledge Tracing Model Progression

```
M3.2: BKT (Hidden Markov Model)
         ↓ works but assumes skill independence
M3.4: DKT (LSTM sequence model)
         ↓ captures temporal patterns, no graph structure
M3.5: GNN (Graph Attention Network)
         ↓ captures graph structure, propagates mastery
M3.6: BKT || DKT+GNN (factory pattern)
         Production uses DKT+GNN
         BKT remains for research comparison
         Paper Section 4: quantitative comparison table
```

---

## Architecture Decision Records Summary

| ADR | Decision | Phase |
|-----|----------|-------|
| ADR-001 | FastAPI over Flask/Django: native async, auto-docs, Pydantic v2 | M1.1 ✅ |
| ADR-002 | Redis for sessions: sub-ms latency, native TTL, pub/sub ready | M1.2 ✅ |
| ADR-003 | Neo4j for knowledge graph: Cypher traversal, GDS algorithms, GNN input | M3.3 |
| ADR-004 | Graph-RAG over vector RAG: prerequisite-aware retrieval, research novelty | M4.2 |
| ADR-005 | PyTorch over TensorFlow: research standard, PyG for GNN, DKT reference code | M3.4+ |
| ADR-006 | DKT (production) + BKT (baseline): progressive complexity, paper comparison | M3.2–M3.6 |
| ADR-007 | GNN (GAT) for competency: propagation, unobserved skill prediction, embeddings | M3.5 |

---

## Research Contributions (for IEEE/ACM Paper)

1. **Novel Problem Framing** — AI-powered adaptive technical interview assessment
2. **Graph-Structured Knowledge Representation** — Skill prerequisite graph drives all decisions
3. **DKT + GNN Combination** — Temporal sequence modeling + structural graph propagation
4. **Graph-RAG for Question Selection** — Graph-aware retrieval over flat vector search
5. **Quantitative Comparison** — BKT vs DKT vs GNN+DKT on custom interview dataset

---

> **Status**: Phase 2, M2.1 Complete → Phase 2, M2.2 Answer Processing Pipeline.
