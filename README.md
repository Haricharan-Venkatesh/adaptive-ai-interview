# Adaptive AI Interview Assistant

An intelligent, closed-loop technical interview assistant designed to dynamically assess candidate knowledge in software engineering domains through adaptive text-based (later extensible to voice/video) questioning.

---

## 🚀 Key Features
- **Adaptive Questioning**: Dynamically selects optimal questions based on the candidate's active knowledge state.
- **Multimodal Evaluation**: Analyzes candidate answers using LLMs (Gemini/OpenAI) combined with Python AST analysis.
- **Dynamic Competency Modeling**: Leverages a NetworkX skill graph combined with Deep Knowledge Tracing (LSTM) and Graph Neural Networks (GNN GAT) to model unobserved candidate skills.
- **Graph-RAG Retrieval**: Graph-aware retrieval of technical questions based on conceptual prerequisites.

---

## 🛠️ Technology Stack
- **Backend**: FastAPI (Python 3.12+), SQLAlchemy 2.0, Alembic, Pydantic v2, structlog.
- **Caching & Sessions**: Redis.
- **Knowledge Graph**: Neo4j.
- **AI/ML Modeling**: PyTorch, PyTorch Geometric (PyG).
- **Frontend**: Next.js 15, TypeScript, Tailwind CSS, Monaco Editor.

---

## 📈 Development Roadmap & Status

### Phase 1 — Foundation
- [x] **M1.1: FastAPI Foundation** (health, config, logging, tests) `✅ Complete (commit c06068a)`
- [x] **M1.2: Redis Session Management** `✅ Complete (commit f8df7a0)`
- [x] **M1.3: Question Database & Seed Data** `✅ Complete (commit 467420a)`
- [ ] **M1.4: GitHub OAuth Authentication** `🔲 NEXT`
- [ ] **M1.5: Next.js Frontend + Chat UI** `🔲`

### Phase 2 — Answer Processing
- [ ] **M2.1: LLM Integration** (Gemini/OpenAI wrapper)
- [ ] **M2.2: Answer Processing Pipeline** (Evaluation scoring)
- [ ] **M2.3: AST-based Code Analysis**

### Phase 3 — Dynamic Modeling
- [ ] **M3.1: NetworkX In-Memory Skill Graph**
- [ ] **M3.2: BKT Baseline** (Bayesian Knowledge Tracing)
- [ ] **M3.3: Neo4j Graph Persistence**
- [ ] **M3.4: Deep Knowledge Tracing** (PyTorch LSTM)
- [ ] **M3.5: Graph Neural Network** (PyTorch Geometric GAT)
- [ ] **M3.6: Production Swap** (Factory-based model switching)

### Phase 4 — Adaptive Question Selection
- [ ] **M4.1: Vector Embeddings** (sentence-transformers & ChromaDB)
- [ ] **M4.2: Graph-RAG Retrieval**
- [ ] **M4.3: Adaptive Question Selection Engine**

### Phase 5 — Output Layer
- [ ] **M5.1: Report Generation Pipeline**
- [ ] **M5.2: Recruiter Dashboard**
- [ ] **M5.3: Graph Visualization** (D3.js/Cytoscape.js)

### Phase 6 — Production
- [ ] **M6.1: Full Testing Suite** (≥80% coverage)
- [ ] **M6.2: Docker & Docker Compose**
- [ ] **M6.3: CI/CD** (GitHub Actions)
- [ ] **M6.4: Performance Evaluation**
- [ ] **M6.5: Research Paper Draft**

---

## 📁 Repository Structure
```
adaptive-ai-interview/
├── backend/            # FastAPI Python Backend
├── frontend/           # Next.js 15 TypeScript Frontend
├── docs/               # Architecture Decision Records (ADRs) & documentation
├── notebooks/          # Jupyter prototypes for KT & GNN models
└── research/           # Reference research papers and experiments
```

For detailed architectural justifications, refer to [Architecture Decision Records](docs/ADR/README.md).
