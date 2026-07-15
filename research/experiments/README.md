# Experiments

This directory documents all experimental comparisons between knowledge tracing models.

## Naming Convention

```
YYYY-MM-DD_experiment-name/
    config.json          — hyperparameters used
    results.json         — metrics output
    notes.md             — observations and analysis
    plots/               — generated figures
```

## Planned Experiments

| ID | Experiment | Models Compared | Metric |
|----|-----------|-----------------|--------|
| E001 | Knowledge Tracing Comparison | BKT vs DKT | AUC, RMSE |
| E002 | GNN vs DKT for skill propagation | GNN vs DKT | AUC, F1 |
| E003 | RAG vs Graph-RAG question quality | Traditional RAG vs Graph-RAG | BLEU, Human eval |
| E004 | Adaptive vs random question selection | Adaptive vs Random | Interview duration, accuracy |
