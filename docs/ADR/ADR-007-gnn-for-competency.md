# ADR-007: Use Graph Neural Networks for Competency Modeling

| Field | Value |
|-------|-------|
| **ID** | ADR-007 |
| **Date** | 2026-07-15 |
| **Status** | Accepted |
| **Implemented In** | Phase 3, Milestone 3.5 |
| **Decided By** | Lead Architect |

---

## Context

The Adaptive AI Interview Assistant models candidate competency as a **graph** where:
- Nodes = skills/concepts (e.g., "Binary Search", "Heap", "Graph Traversal")
- Edges = prerequisite relationships (e.g., "Graph Traversal requires Graph Representation")
- Node attributes = candidate's observed performance on that skill (correctness, confidence)

The system needs to:
1. **Propagate knowledge** — if a candidate masters "Recursion", their estimated probability
   of knowing "DFS" should increase (because DFS requires Recursion)
2. **Predict unobserved skill mastery** — estimate how well the candidate would perform on
   skills they haven't been asked about yet (link prediction in the graph)
3. **Estimate question complexity** — predict how hard a question is for THIS candidate,
   not based on a fixed difficulty label, but based on the candidate's current graph state
4. **Generate skill embeddings** — encode each skill as a dense vector that captures its
   relationship to other skills

DKT (ADR-006) handles the **temporal sequence** of answers well but ignores the **graph structure**
of skill relationships. These two models are complementary, not competing.

---

## Problem

How should we model the structural, graph-based aspects of candidate competency?

---

## Options Considered

### Option A: Rule-based graph traversal
- Manually define propagation rules: "If parent skill is mastered, increase child skill estimate by 20%"
- **Advantage**: Interpretable, no training required
- **Problem**: Rules are manually crafted and don't generalize. The "20%" is arbitrary and not
  learned from data. Does not capture complex multi-hop relationships.

### Option B: Matrix Factorization / Collaborative Filtering
- Represent candidates × skills as a matrix and factorize
- Used in traditional recommender systems (Netflix prize)
- **Problem**: Doesn't explicitly model the graph structure of skill prerequisites.
  Cannot propagate through prerequisite edges.

### Option C: Node2Vec / DeepWalk (Graph Embedding)
- Random walk-based methods that produce node embeddings
- Capture structural similarity between nodes
- **Problem**: These are transductive — cannot generalize to new candidate nodes.
  Also, they ignore node features (candidate's performance data).

### Option D: Graph Neural Networks (GNN) ✅
- **GCN (Graph Convolutional Network)** — aggregates neighbor features through convolution
- **GAT (Graph Attention Network)** — learns which neighbors are most important via attention
- **GraphSAGE** — inductive, generalizes to unseen nodes (critical for new candidates)
- Uses PyTorch Geometric (M3.5, see ADR-005)
- Explicitly models the graph structure AND learns from candidate performance features

---

## Decision

**Implement a GNN using PyTorch Geometric for competency propagation, complexity estimation,
and skill embedding generation.**

### Architecture Design

```
Input: Skill graph G with node features x_v (candidate performance on each skill)
Architecture: 2-layer Graph Attention Network (GAT)
  Layer 1: GAT(in_channels=skill_feature_dim, out_channels=64, heads=4)
  Layer 2: GAT(in_channels=256, out_channels=32, heads=1)
Output:
  - Node embeddings: 32-dim vector per skill node
  - Mastery prediction: sigmoid(Linear(32)) → P(mastery) per node
  - Complexity score: sigmoid(Linear(32)) → difficulty for this candidate
```

### Why GAT over GCN

GAT (Graph Attention Network) is preferred because:
- Not all prerequisite relationships are equally important
- GAT learns attention weights: "Recursion is 3× more important than Big-O notation for predicting DFS mastery"
- More expressive than GCN with minimal overhead

---

## Advantages

1. **Competency propagation** — GNN naturally propagates mastery through the graph.
   If a candidate demonstrates strong Recursion, the GNN updates BFS, DFS, and Tree Traversal
   nodes — even if those skills were never directly tested.

2. **Handles unobserved skills** — Inductive GNNs (GraphSAGE, GAT) estimate mastery for
   skills not yet covered in the interview, enabling smarter question selection.

3. **Research novelty** — Combining GNN-based competency modeling with DKT sequence modeling
   is the primary technical novelty of this project. The two models are complementary:
   - DKT: "Given this candidate's answer sequence, what is their overall trajectory?"
   - GNN: "Given the skill graph structure, how does mastery of one skill predict others?"

4. **Embeds skills for retrieval** — The 32-dim skill embeddings from the GNN can be used
   in the Graph-RAG pipeline (M4.2) to improve question retrieval beyond simple keyword matching.

5. **Complexity estimation** — The GNN produces a personalized difficulty score: a question
   about "AVL Trees" might be difficulty 8/10 for a candidate who has weak BST foundations,
   but 4/10 for one who has demonstrated strong BST mastery.

---

## Disadvantages

1. **Training data requirement** — The GNN must be trained on candidate × skill interaction
   data. We use public KT datasets (ASSISTments) for pre-training, then fine-tune on our
   interview data.

2. **GPU for training** — Training requires a GPU (Google Colab is acceptable for research).
   Inference runs on CPU.

3. **Complexity** — GNNs are harder to debug and explain than BKT. Mitigation: keep BKT
   and DKT as interpretable comparisons (ADR-006).

4. **Graph must be pre-built** — The skill dependency graph (Neo4j, ADR-003) must be
   populated before GNN training. This creates a dependency between M3.3 and M3.5.

---

## Integration with DKT (ADR-006)

The final production system uses BOTH DKT and GNN together:

```
Candidate Answer → DKT → Temporal State Update
                        ↓
                   Graph Update (NetworkX / Neo4j)
                        ↓
                   GNN → Node Embeddings → Propagated Mastery Scores
                        ↓
                   Adaptive Selector → Next Question
```

DKT handles **when** and **how quickly** a candidate learns.
GNN handles **which other skills** that learning implies mastery of.

---

## Future Implications

- In M3.6, the unified `KnowledgeTracerFactory` will return either BKT, DKT, or DKT+GNN
- Model weights are stored in `ai_models/graph_neural_net/` and `ai_models/knowledge_tracing/`
- The GNN + DKT combination is the primary contribution in the IEEE/ACM paper's
  "Method" section, distinguishing this work from prior art (plain DKT or plain GNN systems)
- Future extension: replace GAT with a Graph Transformer for even stronger performance
