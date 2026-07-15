# ADR-004: Use Graph-RAG Instead of Traditional Vector RAG

| Field | Value |
|-------|-------|
| **ID** | ADR-004 |
| **Date** | 2026-07-15 |
| **Status** | Accepted |
| **Implemented In** | Phase 4, Milestone 4.2 |
| **Decided By** | Lead Architect |

---

## Context

The Adaptive Question Selection Engine (Module 2.6 in the architecture diagram) needs to retrieve
the **optimal next question** from the question bank given the current candidate state.

"Optimal" means the question should:
1. Target a concept the candidate has not yet demonstrated mastery in
2. Be at an appropriate difficulty given their current skill level
3. Relate to the concepts they have already answered (context continuity)
4. Not repeat topics already covered in this session

This retrieval problem has a **graph-structured** component (skill prerequisites,
topic relationships) that traditional vector similarity search cannot capture.

---

## Problem

How should we retrieve the most relevant next question given the candidate's current knowledge state?

---

## Options Considered

### Option A: Random Sampling with Difficulty Filter
- Simple: `SELECT * FROM questions WHERE difficulty = :level ORDER BY RANDOM() LIMIT 1`
- Zero infrastructure
- **Problem**: No personalization. No skill gap targeting. Research papers consistently
  show 30-40% efficiency loss vs adaptive selection.

### Option B: Traditional Vector RAG (Dense Retrieval)
- Embed all questions into a vector space (e.g., using `sentence-transformers`)
- At retrieval time, embed the current context and find nearest neighbors by cosine similarity
- **Advantage**: Finds semantically similar questions
- **Problem**: Vector similarity captures semantic closeness but NOT prerequisite structure.
  A question about "AVL Tree rotations" may be semantically close to "Binary Tree traversal"
  but the prerequisite structure says traversal must come first.
- **Problem**: The candidate's competency graph (which nodes are mastered, which are gaps)
  is NOT encoded in the vector space. The retrieval is context-blind to graph state.

### Option C: Graph-RAG ✅
- Combines **graph traversal** (Cypher queries on Neo4j) with **vector similarity** (embeddings)
- Step 1: Traverse the competency graph to identify candidate's skill gaps and mastered skills
- Step 2: Use graph structure to determine which skill gaps are next in prerequisite order
- Step 3: Filter the question bank to questions targeting those specific skills
- Step 4: Within the filtered set, use vector similarity to pick the most contextually appropriate question
- Step 5: If no good match, use LLM to generate a targeted question (Module 2.6)

This approach was validated by Microsoft Research in their 2024 paper "From Local to Global:
A Graph RAG Approach to Query-Focused Summarization" and is increasingly standard in
production knowledge systems.

---

## Decision

**Use Graph-RAG: graph traversal + vector filtering + LLM generation fallback.**

---

## Advantages

1. **Prerequisite-aware retrieval** — The graph structure enforces pedagogically correct
   question ordering. The system cannot ask "Implement a Red-Black Tree" to a candidate
   who has not yet demonstrated basic Binary Tree knowledge.

2. **Knowledge gap targeting** — Graph traversal directly identifies which skills the
   candidate lacks confidence in, making every retrieved question maximally informative.

3. **Research novelty** — Applying Graph-RAG to adaptive educational assessment is novel.
   Standard educational RAG systems use flat vector retrieval. Our graph-structured approach
   is the primary research contribution of this project.

4. **Reduced hallucination risk** — Constraining LLM question generation to specific graph
   nodes (skills) reduces off-topic or inappropriate question generation.

5. **Explainability** — We can explain WHY a question was selected: "This question targets
   the skill gap in Heap operations, which is a prerequisite for the upcoming Priority Queue topic."

---

## Disadvantages

1. **Complexity** — Requires both Neo4j (for graph queries) and a vector store (for embeddings).
2. **Latency** — Two-stage retrieval (graph + vector) is slower than pure vector search.
   Mitigation: cache frequent graph traversal results in Redis.
3. **Cold start** — The graph must be pre-populated before retrieval works correctly.
   This is addressed in M1.3 (seed data) and M3.3 (Neo4j initialization).

---

## Future Implications

- In M4.1, we embed all seed questions into ChromaDB/pgvector
- In M4.2, the Graph-RAG pipeline connects Neo4j traversal → vector filtering → LLM fallback
- This architecture is directly publishable as the core contribution of our IEEE/ACM paper:
  "Graph-Augmented Adaptive Question Selection for AI-Powered Technical Interviews"
