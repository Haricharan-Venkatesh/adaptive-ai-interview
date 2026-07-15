# Research Papers

This directory stores research papers relevant to the Adaptive AI Interview Assistant project.

## Subdirectory Purpose

- `papers/` — PDF copies or links of papers we reference or build upon
- `experiments/` — Documented experimental results comparing models (BKT vs DKT vs GNN)
- `benchmarks/` — Benchmark datasets and scoring scripts
- `datasets/` — Curated interview datasets for training and evaluation

## Key Papers to Reference

1. **Deep Knowledge Tracing** — Piech et al., NeurIPS 2015
   - The foundational paper for our M3.4 LSTM implementation
   - https://arxiv.org/abs/1506.05908

2. **Graph Neural Networks** — Kipf & Welling, ICLR 2017
   - Foundation for our M3.5 GNN competency model
   - https://arxiv.org/abs/1609.02907

3. **Knowledge Tracing Machines** — Vie & Kashima, AAAI 2019
   - Bridges BKT and DKT — important comparison baseline

4. **Graph-RAG** — Edge et al., Microsoft 2024
   - Foundation for our M4.2 Graph-RAG implementation

5. **Computerized Adaptive Testing** — Wainer, 2000
   - Theoretical basis for adaptive question selection

## Experimental Tracking

All experiments comparing BKT vs DKT vs GNN should be documented in `experiments/`
with the following schema:
- Model name
- Dataset used
- Metrics: AUC, RMSE, Accuracy, F1
- Training time
- Inference latency
- Notes
