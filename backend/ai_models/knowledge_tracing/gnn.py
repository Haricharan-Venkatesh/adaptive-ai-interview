import torch
import torch.nn as nn
from pydantic import BaseModel, Field

# Lazy import to handle potential missing dependency gracefully
try:
    from torch_geometric.data import Data
    from torch_geometric.nn import GATConv
    HAS_PYG = True
except ImportError:
    HAS_PYG = False
    GATConv = None
    Data = None

class GNNParams(BaseModel):
    num_skills: int = Field(..., description="Number of unique skills in the graph")
    feature_dim: int = Field(default=1, description="Dimension of node features (e.g. 1 for scalar mastery)")
    hidden_dim: int = Field(default=64, description="Hidden dimension for GAT Layer 1")
    embedding_dim: int = Field(default=32, description="Output embedding dimension for GAT Layer 2")


class GATCompetencyModel(nn.Module):
    """
    Graph Attention Network (GAT) for propagating skill mastery through a prerequisite graph.
    """
    def __init__(self, feature_dim: int = 1, hidden_dim: int = 64, embedding_dim: int = 32):
        super().__init__()
        if not HAS_PYG:
            raise RuntimeError("torch-geometric is not installed. Cannot instantiate GATCompetencyModel.")
            
        # First layer: expand features, use multiple attention heads
        self.conv1 = GATConv(in_channels=feature_dim, out_channels=hidden_dim, heads=4, concat=True)
        
        # Second layer: compress back down to embedding_dim, use 1 head
        # In GAT, if concat=True in prev layer, the input to next is out_channels * heads
        self.conv2 = GATConv(in_channels=hidden_dim * 4, out_channels=embedding_dim, heads=1, concat=False)
        
        # Output heads
        self.mastery_head = nn.Linear(embedding_dim, 1)
        self.complexity_head = nn.Linear(embedding_dim, 1)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> dict[str, torch.Tensor]:
        """
        Args:
            x: Node feature matrix of shape (num_nodes, feature_dim)
            edge_index: Graph connectivity matrix of shape (2, num_edges)
            
        Returns:
            Dictionary containing:
                - 'embeddings': Node embeddings (num_nodes, embedding_dim)
                - 'mastery_probs': Propagated mastery probability per node (num_nodes, 1)
                - 'complexity_scores': Question complexity score per node (num_nodes, 1)
        """
        # Layer 1
        h = self.conv1(x, edge_index)
        h = torch.relu(h)
        
        # Layer 2
        embeddings = self.conv2(h, edge_index)
        
        # Heads
        mastery_logits = self.mastery_head(embeddings)
        complexity_logits = self.complexity_head(embeddings)
        
        mastery_probs = torch.sigmoid(mastery_logits)
        complexity_scores = torch.sigmoid(complexity_logits)
        
        return {
            "embeddings": embeddings,
            "mastery_probs": mastery_probs,
            "complexity_scores": complexity_scores
        }


class GNNKnowledgePropagator:
    """
    Wrapper for using the GATCompetencyModel.
    Converts domain data into PyTorch Geometric format and runs inference.
    """
    def __init__(self, model_path: str | None = None, num_skills: int = 100):
        self.params = GNNParams(num_skills=num_skills)
        self.model = GATCompetencyModel(
            feature_dim=self.params.feature_dim,
            hidden_dim=self.params.hidden_dim,
            embedding_dim=self.params.embedding_dim
        )
        self.model.eval()
        
        if model_path:
            self.model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
            
    def propagate(self, mastery_estimates: list[float], edge_index_list: list[list[int]]) -> dict[str, torch.Tensor]:
        """
        Propagates mastery through the graph.
        
        Args:
            mastery_estimates: List of length num_skills containing initial mastery estimates [0, 1]
                               For unobserved skills, this might be a default prior (e.g. 0.5)
            edge_index_list: A list of two lists [[source_nodes], [target_nodes]] representing directed edges.
                             e.g. [[0, 1], [1, 2]] means 0->1 and 1->2.
                             
        Returns:
            Dictionary with 'embeddings', 'mastery_probs', and 'complexity_scores'
        """
        if len(mastery_estimates) != self.params.num_skills:
            raise ValueError(f"Expected {self.params.num_skills} estimates, got {len(mastery_estimates)}")
            
        # Convert inputs to tensors
        x = torch.tensor(mastery_estimates, dtype=torch.float32).unsqueeze(1) # Shape (num_skills, 1)
        
        if edge_index_list and len(edge_index_list[0]) > 0:
            edge_index = torch.tensor(edge_index_list, dtype=torch.long)
        else:
            # Empty graph case: create a dummy empty edge_index of shape (2, 0)
            edge_index = torch.empty((2, 0), dtype=torch.long)
            
        with torch.no_grad():
            outputs = self.model(x, edge_index)
            
        return outputs
