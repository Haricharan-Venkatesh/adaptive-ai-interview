# Architecture Decision Records (ADRs)

## What is an ADR?

An Architecture Decision Record documents a significant architectural decision made during the
project, along with its context, the options that were considered, and the reasoning behind the
final choice.

ADRs are a standard practice at companies like GitHub, Netflix, Amazon, and Google.
They are especially important for research projects submitted to IEEE/ACM because reviewers
and future maintainers need to understand **why** a technology was chosen, not just what was chosen.

## Status Lifecycle

- **Proposed** — Under consideration, not yet implemented
- **Accepted** — Decision made, implementation in progress
- **Deprecated** — Still in use but superseded by a newer decision
- **Superseded** — Replaced entirely by another ADR

## ADR Index

| ID | Title | Status | Phase |
|----|-------|--------|-------|
| [ADR-001](ADR-001-fastapi-over-flask.md) | FastAPI over Flask/Django | Accepted | M1.1 |
| [ADR-002](ADR-002-redis-for-sessions.md) | Redis for Session Management | Accepted | M1.2 |
| [ADR-003](ADR-003-neo4j-for-graph.md) | Neo4j for Knowledge Graph | Accepted | M3.3 |
| [ADR-004](ADR-004-graph-rag-over-vector-rag.md) | Graph-RAG over Traditional RAG | Accepted | M4.2 |
| [ADR-005](ADR-005-pytorch-over-tensorflow.md) | PyTorch over TensorFlow | Accepted | M3.4 |
| [ADR-006](ADR-006-dkt-over-bkt.md) | Deep Knowledge Tracing over Bayesian Knowledge Tracing | Accepted | M3.6 |
| [ADR-007](ADR-007-gnn-for-competency.md) | Graph Neural Networks for Competency Modeling | Accepted | M3.5 |

## How to Create a New ADR

1. Copy the template from `ADR-000-template.md`
2. Name it `ADR-NNN-short-title.md`
3. Fill in all sections
4. Add it to the index table above
5. Link it from the relevant milestone in `implementation_plan.md`
