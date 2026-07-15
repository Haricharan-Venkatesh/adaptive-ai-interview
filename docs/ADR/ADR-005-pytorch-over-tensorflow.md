# ADR-005: Use PyTorch Instead of TensorFlow

| Field | Value |
|-------|-------|
| **ID** | ADR-005 |
| **Date** | 2026-07-15 |
| **Status** | Accepted |
| **Implemented In** | Phase 3, Milestones 3.4 and 3.5 |
| **Decided By** | Lead Architect |

---

## Context

The system requires two ML model implementations:

1. **M3.4 — Deep Knowledge Tracing (DKT)**: An LSTM-based sequence model that predicts
   the probability of a candidate answering a question correctly given their answer history.

2. **M3.5 — Graph Neural Network (GNN)**: A graph convolutional network implemented
   with PyTorch Geometric that learns skill embeddings and propagates competency through
   the skill graph.

Both models require a deep learning framework. The two dominant choices are PyTorch and TensorFlow.

---

## Problem

Which deep learning framework should we use for DKT and GNN implementations?

---

## Options Considered

### Option A: TensorFlow / Keras
- Developed by Google Brain
- Excellent production deployment story (TensorFlow Serving, TFLite)
- Keras API is beginner-friendly
- **Problem**: Dynamic graph (eager execution) came late (TF 2.0) and is still less
  Pythonic than PyTorch for research
- **Problem**: Graph Neural Networks are second-class citizens in TensorFlow.
  TensorFlow GNN (TF-GNN) is less mature and has a smaller community than PyTorch Geometric
- **Problem**: Debugging is harder — TF's execution graph is less transparent

### Option B: PyTorch ✅
- Developed by Meta AI Research
- **De-facto standard for academic research** — PyTorch is used in > 70% of NeurIPS,
  ICML, and ICLR papers
- **PyTorch Geometric (PyG)** — the dominant library for Graph Neural Networks, with
  native support for GCN, GAT, GraphSAGE, and message passing frameworks
- **Dynamic computation graphs** — debugging is natural: use Python debugger, print tensors
- **Pythonic API** — feels like NumPy, easy to learn
- **ONNX export** — models can be exported for deployment on any runtime

---

## Decision

**Use PyTorch for DKT (M3.4) and PyTorch Geometric for GNN (M3.5).**

---

## Advantages

1. **Research standard** — Reviewers of IEEE/ACM papers expect PyTorch for novel model
   implementations. Using TensorFlow would require justification.

2. **PyTorch Geometric** — PyG provides pre-built graph convolution layers (GCNConv, GATConv),
   message passing API, and graph batch utilities. Implementing GNN from scratch in TF would
   take 5× longer.

3. **DKT reference implementations** — The original Deep Knowledge Tracing paper code
   (Piech et al., NeurIPS 2015) is in PyTorch. Community implementations, pre-trained
   checkpoints, and follow-up work (DKVMN, SAINT) are all PyTorch-first.

4. **Developer experience** — `model.parameters()`, `optimizer.step()`, custom loss functions
   are all simpler in PyTorch. For a research project where the models will be iterated on
   frequently, this velocity advantage is critical.

5. **Unified framework** — Using one framework for both LSTM (DKT) and GNN prevents
   framework mismatch issues and simplifies the `requirements.txt`.

---

## Disadvantages

1. **Production deployment** — TensorFlow Serving is more mature for serving.
   Mitigation: use `torchserve` or ONNX export for production deployment in M6.
2. **Mobile/edge** — TFLite is better for edge deployment. Not relevant for this project.

---

## Future Implications

- In M3.4, implement DKT as a standard PyTorch `nn.Module` with LSTM layers.
- In M3.5, implement GNN using `torch_geometric.nn.GCNConv` or `GATConv`.
- In M3.6, the DKT and GNN models replace BKT in the production knowledge tracer,
  while BKT remains available as a `--baseline` flag for research comparison.
- Model artifacts are saved as `.pt` files and versioned in `ai_models/`.
- For model serving in production, wrap in a FastAPI endpoint using `torch.inference_mode()`.
