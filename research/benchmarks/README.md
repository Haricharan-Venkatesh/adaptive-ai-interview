# Benchmarks

Benchmark scripts and evaluation harnesses for comparing models.

## Planned Benchmarks

- `kt_benchmark.py` — Knowledge Tracing model comparison (BKT / DKT / GNN)
- `rag_benchmark.py` — RAG retrieval quality evaluation
- `interview_quality.py` — End-to-end interview quality scoring

## Metrics Used

| Metric | Used For | Interpretation |
|--------|----------|---------------|
| AUC-ROC | KT models | Higher = better prediction of correctness |
| RMSE | KT models | Lower = better calibration |
| BLEU-4 | Question generation | Higher = more coherent questions |
| MRR | RAG retrieval | Higher = better ranking of relevant questions |
| Interview Score δ | Adaptive engine | How much faster convergence vs random |
