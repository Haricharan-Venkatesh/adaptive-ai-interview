# Notebooks

Jupyter notebooks for exploration, prototyping, and visualization.

## Organization

```
notebooks/
├── 01_data_exploration/       — Dataset analysis and statistics
├── 02_bkt_prototype/          — Bayesian Knowledge Tracing baseline
├── 03_dkt_prototype/          — Deep Knowledge Tracing development
├── 04_gnn_prototype/          — Graph Neural Network prototyping
├── 05_rag_experiments/        — RAG vs Graph-RAG comparison
└── 06_report_analysis/        — Interview report quality analysis
```

## Naming Convention

```
NNN_short_description.ipynb
e.g. 001_dataset_statistics.ipynb
     002_bkt_implementation.ipynb
```

## Workflow

Notebooks are for **exploration only**.
Once a concept is validated here, move it to the backend service layer.
Never import from notebooks in production code.

## Running Notebooks

```bash
# From project root
cd notebooks
pip install jupyter
jupyter lab
```
