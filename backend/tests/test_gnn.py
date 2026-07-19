
import pytest
import torch

from ai_models.knowledge_tracing.gnn import (
    HAS_PYG,
    GATCompetencyModel,
    GNNKnowledgePropagator,
    GNNParams,
)

pytestmark = pytest.mark.skipif(not HAS_PYG, reason="torch-geometric is not installed")

def test_gnn_params():
    params = GNNParams(num_skills=10)
    assert params.num_skills == 10
    assert params.feature_dim == 1
    assert params.hidden_dim == 64
    assert params.embedding_dim == 32

def test_gat_competency_model_forward():
    if not HAS_PYG:
        return
        
    num_nodes = 5
    feature_dim = 1
    
    model = GATCompetencyModel(feature_dim=feature_dim, hidden_dim=8, embedding_dim=4)
    
    # Node features: column vector of 1s
    x = torch.ones((num_nodes, feature_dim), dtype=torch.float32)
    
    # Edges: 0->1, 1->2, 2->3, 3->4
    edge_index = torch.tensor([
        [0, 1, 2, 3],
        [1, 2, 3, 4]
    ], dtype=torch.long)
    
    outputs = model(x, edge_index)
    
    assert "embeddings" in outputs
    assert "mastery_probs" in outputs
    assert "complexity_scores" in outputs
    
    assert outputs["embeddings"].shape == (num_nodes, 4)
    assert outputs["mastery_probs"].shape == (num_nodes, 1)
    assert outputs["complexity_scores"].shape == (num_nodes, 1)
    
    # Probs should be in [0, 1]
    assert torch.all(outputs["mastery_probs"] >= 0.0)
    assert torch.all(outputs["mastery_probs"] <= 1.0)


def test_gnn_knowledge_propagator():
    if not HAS_PYG:
        return
        
    num_skills = 3
    propagator = GNNKnowledgePropagator(num_skills=num_skills)
    
    # 1. Test invalid length
    with pytest.raises(ValueError):
        propagator.propagate([0.5, 0.5], [])
        
    # 2. Test empty graph
    mastery = [0.1, 0.5, 0.9]
    outputs = propagator.propagate(mastery, [])
    assert outputs["mastery_probs"].shape == (3, 1)
    
    # 3. Test graph with edges (0->1, 1->2)
    edges = [
        [0, 1],
        [1, 2]
    ]
    outputs = propagator.propagate(mastery, edges)
    assert outputs["mastery_probs"].shape == (3, 1)
    assert outputs["embeddings"].shape == (3, propagator.params.embedding_dim)
