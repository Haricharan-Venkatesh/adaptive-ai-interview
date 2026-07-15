# ADR-003: Use Neo4j for the Knowledge Graph

| Field | Value |
|-------|-------|
| **ID** | ADR-003 |
| **Date** | 2026-07-15 |
| **Status** | Accepted |
| **Implemented In** | Phase 3, Milestone 3.3 |
| **Decided By** | Lead Architect |

---

## Context

The Adaptive AI Interview Assistant models candidate knowledge as a **graph**:
- Nodes represent skills/concepts (e.g., "Binary Trees", "Recursion", "DFS")
- Edges represent relationships (e.g., "DFS requires Recursion", "Binary Trees uses DFS")
- Edge weights represent the strength of prerequisite dependency

This graph drives the adaptive question selection engine (Module 2.4 in the architecture diagram):
- Competency Gap Analysis traverses the graph to find skills not yet assessed
- Difficulty Adaptation follows prerequisite edges to ensure foundational skills are tested first
- Information Gain Estimation ranks nodes by how much new information testing them would provide

The graph is also the primary artifact for the **research contribution**: we are demonstrating
that graph-structured knowledge representation produces better adaptive interviews than flat
difficulty tiers.

---

## Problem

Where should we store and query the candidate skill graph?

---

## Options Considered

### Option A: PostgreSQL with adjacency list / JSON columns
- Use a `skills` table with a `prerequisites` JSON column
- Simple to implement using existing PostgreSQL (M1.3)
- **Problem**: Graph traversal (multi-hop queries) requires recursive CTEs or application-level
  iteration. A query like "find all skills reachable within 2 hops from Binary Trees" is painful.
- No native graph algorithms (PageRank, shortest path, community detection)
- Does not scale for deep graphs (6+ hops)

### Option B: NetworkX (Python in-memory graph)
- Already planned for M3.1 as the baseline skill graph
- Perfect for development, prototyping, and single-interview analysis
- **Problem**: Not persistent. Rebuilding the graph on every restart is expensive.
- Not queryable by external tools (recruiter dashboard cannot query a Python object)
- No native support for distributed multi-user sessions

### Option C: Apache TinkerPop / Gremlin
- Graph query standard, works with Amazon Neptune, CosmosDB
- Steep learning curve
- Overkill for a research prototype

### Option D: Neo4j ✅
- **Purpose-built graph database** — the world's most widely used graph database
- **Cypher query language** — human-readable graph query language:
  `MATCH (s:Skill)-[:REQUIRES]->(p:Skill) WHERE s.name = 'DFS' RETURN p`
- **Native graph storage** — stored and indexed as a graph, not rows/columns
- **Built-in graph algorithms** — PageRank, centrality, community detection (via GDS plugin)
- **Python driver** — async-compatible neo4j Python driver
- **GraphQL integration** — exportable to the frontend graph visualization
- **Academic credibility** — used in research papers, including knowledge graph papers

---

## Decision

**Use Neo4j for persistent graph storage and Cypher-based graph queries.**
**Use NetworkX (M3.1) as the in-memory working graph during an interview session.**

The two-layer architecture:
```
Redis (live session) → NetworkX (in-memory graph ops) → Neo4j (persistent graph store)
```

At session start: load candidate graph from Neo4j into NetworkX.
During interview: update NetworkX in-memory.
At session end: persist updated graph back to Neo4j.

---

## Advantages

1. **Native multi-hop traversal** — "Find all skills this candidate has not demonstrated,
   that depend on skills they have demonstrated" is one Cypher query vs complex application code.

2. **Graph algorithms** — Neo4j GDS (Graph Data Science) plugin provides PageRank,
   Louvain community detection, and k-NN — directly applicable to skill gap analysis.

3. **Visualization-ready** — Neo4j Browser provides a built-in graph visualization.
   This makes demos and research paper figures easy to generate.

4. **Research publication justification** — Using a dedicated graph database strengthens
   the paper's claim that graph structure is fundamental to our approach. Reviewers expect
   a graph DB when the system claims graph-structured knowledge modeling.

5. **Schema flexibility** — Adding new skill types, relationship types, or metadata
   doesn't require schema migrations (unlike PostgreSQL).

---

## Disadvantages

1. **Operational overhead** — Another database process to manage (mitigated by Docker Compose).
2. **Learning curve** — Cypher is a new query language (but simpler than SQL for graphs).
3. **Memory usage** — Neo4j is JVM-based and requires > 512MB heap in production.
4. **Not relational** — Cannot do joins with the PostgreSQL question bank directly;
   requires application-layer coordination.

---

## Future Implications

- In M3.5 (GNN), we will use the Neo4j graph as the **training data source** for the
  PyTorch Geometric model. The graph structure directly feeds the GNN.
- In M4.2 (Graph-RAG), Cypher queries against Neo4j replace traditional vector similarity
  search for knowledge-aware question retrieval.
- In M5.3 (Visualization), the recruiter dashboard uses Neo4j's exported JSON to render
  the candidate's competency graph using D3.js/Cytoscape.js.
