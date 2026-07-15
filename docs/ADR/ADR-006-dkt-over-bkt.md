# ADR-006: Use Deep Knowledge Tracing as the Production Estimator (BKT as Research Baseline)

| Field | Value |
|-------|-------|
| **ID** | ADR-006 |
| **Date** | 2026-07-15 |
| **Status** | Accepted |
| **Implemented In** | M3.2 (BKT baseline) → M3.4 (DKT) → M3.6 (swap BKT→DKT in production) |
| **Decided By** | Lead Architect |

---

## Context

The Dynamic Competency Modeling Engine (Module 2.3 in the architecture diagram) must maintain
a real-time estimate of what the candidate knows. This is the **knowledge tracing** problem.

Knowledge tracing is defined as: given a sequence of a student's past interactions with
knowledge concepts and their correctness, predict the probability that the student will
answer the next question correctly.

This is a core component of the system and directly affects the quality of adaptive question
selection. A poor knowledge tracer leads to poor adaptive selection, wasted interview time,
and inaccurate candidate reports.

---

## Problem

Which knowledge tracing model should we use in production?

---

## Background: The Knowledge Tracing Problem

Given a student's answer history:
```
[(Recursion, correct), (DFS, incorrect), (BFS, correct), (Recursion, correct), ...]
```
Predict: `P(answer next question about Binary Trees correctly) = ?`

---

## Options Considered

### Option A: Bayesian Knowledge Tracing (BKT) — Research Baseline
- Proposed by Corbett & Anderson (1994) — over 30 years old
- Models each skill as a **Hidden Markov Model** with 4 parameters:
  - P(L₀) — prior probability of knowing the skill
  - P(T) — probability of transitioning from not-knowing to knowing (learning rate)
  - P(G) — probability of guessing correctly (without knowing)
  - P(S) — probability of slipping (knowing but answering incorrectly)
- **Advantages**: Interpretable, fast, no GPU needed, well-studied
- **Disadvantages**:
  - Assumes skills are **independent** — knowing Recursion doesn't help predict BFS performance
  - Parameters must be manually fit per skill — doesn't generalize to unseen skills
  - Cannot capture long-range dependencies in answer sequences
  - AUC on ASSISTments benchmark: ~0.67

### Option B: Deep Knowledge Tracing (DKT) ✅ Production
- Proposed by Piech et al., NeurIPS 2015
- Uses an **LSTM** to model the entire sequence of interactions
- Input: one-hot encoded (skill, correctness) pairs
- Output: probability vector over all skills for the next interaction
- **Advantages**:
  - Automatically captures skill correlations (no independence assumption)
  - Learns from data — no manual parameter fitting per skill
  - Generalizes to unseen skill combinations
  - AUC on ASSISTments benchmark: ~0.82 (+15% over BKT)
- **Disadvantages**:
  - Requires training data (handled by research datasets in M3.4)
  - Black box — less interpretable than BKT
  - Requires GPU for training (inference is CPU-feasible)

### Option C: Knowledge Tracing Machines (KTM)
- Combines BKT structure with factorization machines
- Better than BKT, slightly worse than DKT on most benchmarks
- Less popular in recent literature — harder to build a research story around

### Option D: SAINT (Self-Attentive Knowledge Tracing)
- Transformer-based knowledge tracer (Choi et al., EDM 2020)
- State of the art on large benchmarks
- Requires more training data than DKT
- Appropriate as a future enhancement after DKT is validated

---

## Decision

**Implement BKT in M3.2 as a transparent, interpretable baseline.**
**Implement DKT in M3.4 as the production-grade model.**
**In M3.6, replace the BKT estimator in the production pipeline with DKT,**
**while keeping BKT available via a runtime flag for research comparison.**

```python
# Runtime selection (M3.6 design)
tracer = KnowledgeTracerFactory.create(
    model_type=settings.knowledge_tracer_model,  # "bkt" | "dkt" | "gnn"
)
```

---

## Advantages of This Two-Stage Approach

1. **Research contribution** — Quantitatively comparing BKT vs DKT on our custom
   interview dataset is a core result of the IEEE/ACM paper. Without BKT as a baseline,
   there is nothing to compare against.

2. **Progressive complexity** — BKT is implemented first because it's simpler and
   provides immediate value while DKT training data is being collected.

3. **Risk mitigation** — If DKT training fails or produces poor results, BKT is a
   working fallback. Production systems never have a single point of failure.

4. **Pedagogical value** — Implementing BKT before DKT teaches the fundamental concepts
   of knowledge tracing (Hidden Markov Models, latent state estimation) before introducing
   the neural approach.

5. **Reproducibility** — Our paper's experimental section can report both models on the
   same evaluation set, enabling reproducibility by other researchers.

---

## Disadvantages

1. **Additional implementation time** — Building BKT then DKT takes longer than DKT alone.
   Trade-off accepted: the research value justifies the time investment.

2. **Model management complexity** — Two models must be maintained and versioned.
   Mitigation: `KnowledgeTracerFactory` pattern abstracts this behind a clean interface.

---

## Future Implications

- M3.6 introduces the `KnowledgeTracerFactory` with a `model_type` setting in `.env`
- Experiments comparing BKT vs DKT are documented in `research/experiments/E001_kt_comparison/`
- The comparison results feed directly into Section 4 (Experiments) of the research paper
- SAINT (transformer-based) is identified as a future enhancement beyond M3.6
