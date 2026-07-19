# Adaptive AI Interview Assistant — Task List

---

## Phase 1 — Foundation

### M1.1 FastAPI Foundation ✅ COMPLETE (commit c06068a)
- [x] Create virtual environment (.venv)
- [x] Write pyproject.toml (hatch, ruff, pytest config)
- [x] Write .env + .env.example
- [x] Write app/core/config.py (Pydantic v2 settings)
- [x] Write app/core/logging.py (structlog, JSON/console renderer)
- [x] Write app/models/health.py (HealthResponse, ReadinessResponse, ServiceStatus)
- [x] Write app/api/v1/health.py (liveness + readiness endpoints)
- [x] Write app/api/v1/__init__.py (Router registry pattern)
- [x] Write app/main.py (application factory, lifespan, middleware)
- [x] Write all __init__.py package markers
- [x] Write tests/test_health.py (14 test cases)
- [x] Fix ruff lint issues (unused import, uuid top-level, ruff config section)
- [x] Install dependencies (pip install -e ".[dev]") — DONE
- [x] Run pytest — 14/14 tests PASS
- [x] Run ruff check — zero lint errors
- [x] Commit M1.1 to Git (commit c06068a, 16 files, 802 insertions)

### Architectural Improvements (pre-M1.2) ✅ COMPLETE
- [x] Create research/papers/README.md
- [x] Create research/experiments/README.md
- [x] Create research/benchmarks/README.md
- [x] Create research/datasets/README.md
- [x] Create notebooks/README.md
- [x] Create docs/ADR/README.md (ADR index)
- [x] Write ADR-001 (FastAPI over Flask)
- [x] Write ADR-002 (Redis for sessions)
- [x] Write ADR-003 (Neo4j for knowledge graph)
- [x] Write ADR-004 (Graph-RAG over vector RAG)
- [x] Write ADR-005 (PyTorch over TensorFlow)
- [x] Write ADR-006 (DKT over BKT — progressive model strategy)
- [x] Write ADR-007 (GNN for competency modeling)
- [x] Update implementation_plan.md with expanded Phase 3 (M3.1–M3.6)
- [x] Commit architectural improvements to Git (commit d29a6b4)

### M1.2 Redis Session Management ✅ COMPLETE (commit f8df7a0)
- [x] Add `redis>=5.0.0` to pyproject.toml dependencies
- [x] Add REDIS_URL to .env + .env.example
- [x] Write app/db/redis_client.py
  - [x] Async connection pool with configurable URL
  - [x] `ping()` health check function
  - [x] `get_redis()` dependency for FastAPI injection
- [x] Write app/models/session.py
  - [x] InterviewSession Pydantic model
  - [x] SessionStatus enum (active / paused / completed / expired)
  - [x] QuestionRecord model (question + answer + score + timestamp)
- [x] Write app/services/session_service.py
  - [x] `create_session()` — generate UUID, store in Redis with TTL
  - [x] `get_session()` — retrieve + deserialize
  - [x] `update_session()` — patch specific fields
  - [x] `delete_session()` — explicit cleanup
  - [x] `append_question_record()` — add Q&A to session history
- [x] Write app/api/v1/session.py
  - [x] POST /sessions — create new interview session
  - [x] GET /sessions/{session_id} — retrieve session
  - [x] PATCH /sessions/{session_id} — update session state
  - [x] DELETE /sessions/{session_id} — end session
- [x] Register session router in app/api/v1/__init__.py
- [x] Add Redis check to readiness probe in health.py
- [x] Update app/core/config.py with REDIS_URL, SESSION_TTL_SECONDS
- [x] Write tests/test_session.py (mock Redis with fakeredis)
- [x] Run pytest — all tests PASS
- [x] Run ruff check — zero errors
- [x] Commit M1.2 to Git

### M1.3 Question Database & Seed Data ✅ COMPLETE (commit 467420a)
- [x] Add `sqlalchemy>=2`, `asyncpg`, `alembic` to `pyproject.toml`
- [x] Create postgres DB connection layer in `app/db/postgres.py`
- [x] Create SQLAlchemy models and Pydantic schemas in `app/models/question.py`
- [x] Configure and initialize Alembic migrations
- [x] Create 56 seed questions in JSON dataset
- [x] Create seeder script `backend/scripts/seed_questions.py`
- [x] Create database operations service in `app/services/question_engine.py`
- [x] Expose question endpoints in `app/api/v1/questions.py`
- [x] Update router registry and health check
- [x] Write tests in `tests/test_questions.py`
- [x] Commit M1.3 to Git (commit 467420a)

### M1.4 GitHub OAuth Authentication ✅ COMPLETE (commit 9ec0fce)
- [x] Add python-jose, passlib, authlib to pyproject.toml
- [x] Write app/core/security.py (JWT creation/verification)
- [x] Write app/models/user.py
- [x] Write app/api/v1/auth.py (GitHub OAuth flow)
- [x] Add GITHUB_CLIENT_ID/SECRET to .env.example
- [x] Write tests/test_auth.py
- [x] Commit M1.4 to Git

### M1.5 Next.js Frontend + Chat UI ✅ COMPLETE (commit b19b240)
- [x] Initialize Next.js 15 + TypeScript + Tailwind
- [x] Build landing page (/)
- [x] Build interview chat UI (/interview)
- [x] Monaco code editor component
- [x] Connect to FastAPI backend
- [x] Commit M1.5 to Git

---

## Phase 2 — Answer Processing

### M2.1 LLM Integration ✅ COMPLETE
- [x] Add google-generativeai to pyproject.toml
- [x] Write app/ai/llm_client.py (unified Gemini/OpenAI wrapper)
- [x] Write app/ai/prompts/answer_eval.py
- [x] Write app/ai/prompts/question_gen.py
- [x] Add GEMINI_API_KEY to .env.example
- [x] Commit M2.1 to Git

### M2.2 Answer Processing Pipeline
- [ ] Write app/services/answer_analyzer.py
- [ ] Write app/models/answer.py (EvaluationResult)
- [ ] Write app/api/v1/answers.py
- [ ] Write tests/test_answer_analyzer.py
- [ ] Commit M2.2 to Git

### M2.3 AST-based Code Analysis
- [ ] Write app/services/ast_analyzer.py
- [ ] Integrate with answer_analyzer.py
- [ ] Write tests/test_ast_analyzer.py
- [ ] Commit M2.3 to Git

---

## Phase 3 — Dynamic Modeling (EXPANDED)

### M3.1 NetworkX In-Memory Skill Graph ✅ COMPLETE
- [x] Add networkx to pyproject.toml
- [x] Write app/services/skill_graph.py
- [x] Write app/models/candidate.py
- [x] Commit M3.1 to Git

### M3.2 BKT Baseline (Bayesian Knowledge Tracing) ✅ COMPLETE
- [x] Write backend/ai_models/knowledge_tracing/bkt.py
  - [x] HMM parameters: P(L0), P(T), P(G), P(S) per skill
  - [x] `update(skill, correct)` → posterior update
  - [x] `predict(skill)` → P(correct next)
  - [x] Integration with skill_graph.py
- [x] Write tests/test_bkt.py
- [x] Document in research/experiments/E001_kt_comparison/
- [x] Commit M3.2 to Git

### M3.3 Neo4j Graph Persistence ✅ COMPLETE
- [x] Add neo4j (async driver) to pyproject.toml
- [x] Write app/db/neo4j_client.py
- [x] Write Cypher query helpers
- [x] Add Neo4j check to readiness probe
- [x] Add NEO4J_URI/USER/PASSWORD to .env.example
- [x] Write tests/test_neo4j.py
- [x] Commit M3.3 to Git

### M3.4 Deep Knowledge Tracing (PyTorch LSTM) ← ADR-005, ADR-006 ✅ COMPLETE
- [x] Add torch, torchvision to pyproject.toml
- [x] Write backend/ai_models/knowledge_tracing/dkt.py
  - [x] nn.Module with LSTM + Linear head
  - [x] Input: (skill_id, correctness) sequence
  - [x] Output: P(correct) per skill for next step
  - [x] Training loop with synthetic data (per user instruction)
  - [x] Model checkpoint save/load
- [x] Write training script backend/ai_models/knowledge_tracing/train_dkt.py
- [x] Create notebook: notebooks/03_dkt_prototype/01_dkt_training.ipynb
- [x] Write tests/test_dkt.py
- [x] Commit M3.4 to Git

### M3.5 Graph Neural Network (PyTorch Geometric GAT) ← ADR-005, ADR-007
- [ ] Add torch-geometric to pyproject.toml
- [ ] Write backend/ai_models/graph_neural_net/gat_model.py
  - [ ] 2-layer GAT (GATConv)
  - [ ] Node feature: candidate performance vector
  - [ ] Output: 32-dim node embeddings + mastery prediction + complexity score
  - [ ] Training loop with Neo4j graph data
  - [ ] Checkpoint save/load
- [ ] Write training script backend/ai_models/graph_neural_net/train_gnn.py
- [ ] Create notebook: notebooks/04_gnn_prototype/
- [ ] Write tests/test_gnn.py
- [ ] Commit M3.5 to Git

### M3.6 Production Model Swap + Research Comparison ← ADR-006, ADR-007
- [ ] Write backend/ai_models/knowledge_tracing/factory.py
  - [ ] KnowledgeTracerFactory.create(model_type: "bkt" | "dkt" | "dkt_gnn")
  - [ ] Unified interface: update(skill, correct), predict(skill)
- [ ] Update knowledge_tracer.py service to use factory
- [ ] Add KNOWLEDGE_TRACER_MODEL="dkt_gnn" to .env
- [ ] Run E001 experiment: BKT vs DKT AUC comparison
- [ ] Document results in research/experiments/E001_kt_comparison/
- [ ] Commit M3.6 to Git

---

## Phase 4 — Adaptive Question Selection

### M4.1 Vector Embeddings
- [ ] Add sentence-transformers, chromadb to pyproject.toml
- [ ] Write app/ai/embeddings.py
- [ ] Embed all seed questions on startup
- [ ] Commit M4.1 to Git

### M4.2 Graph-RAG Retrieval ← ADR-004
- [ ] Write app/ai/rag_engine.py (Graph traversal + vector filtering + LLM fallback)
- [ ] Write app/ai/prompts/question_gen.py
- [ ] Create notebook: notebooks/05_rag_experiments/
- [ ] Commit M4.2 to Git

### M4.3 Adaptive Question Selection Engine
- [ ] Write app/services/adaptive_selector.py (full Module 2.4 + 2.5 + 2.6 pipeline)
- [ ] End-to-end interview loop integration
- [ ] Commit M4.3 to Git

---

## Phase 5 — Output Layer

### M5.1 Report Generation
- [ ] Write app/services/report_generator.py
- [ ] Write app/ai/prompts/report_gen.py
- [ ] Write app/api/v1/reports.py
- [ ] Commit M5.1 to Git

### M5.2 Recruiter Dashboard
- [ ] Build dashboard page in Next.js
- [ ] Analytics widgets (score, radar chart)
- [ ] Commit M5.2 to Git

### M5.3 Graph Visualization
- [ ] Integrate D3.js or Cytoscape.js
- [ ] Visualize candidate skill graph
- [ ] Commit M5.3 to Git

---

## Phase 6 — Production

### M6.1 Full Testing Suite
- [ ] Achieve ≥80% test coverage (pytest-cov)
- [ ] Integration tests
- [ ] End-to-end tests

### M6.2 Docker + docker-compose
- [ ] backend/Dockerfile
- [ ] frontend/Dockerfile
- [ ] docker-compose.yml (FastAPI + Redis + PostgreSQL + Neo4j + Frontend)

### M6.3 CI/CD (GitHub Actions)
- [ ] .github/workflows/ci.yml (test + lint on every push)

### M6.4 Performance Evaluation
- [ ] Benchmark interview latency (p50, p95, p99)
- [ ] Adaptive selection efficiency vs random baseline

### M6.5 Research Paper
- [ ] Draft paper structure (IEEE template)
- [ ] System architecture section
- [ ] Experiments section (E001 BKT vs DKT, E002 RAG vs Graph-RAG)
- [ ] Results and discussion
