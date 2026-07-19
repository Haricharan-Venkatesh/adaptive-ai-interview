import torch
import torch.nn as nn
from pydantic import BaseModel, Field


class DKTParams(BaseModel):
    num_skills: int = Field(..., description="Number of unique skills in the domain")
    hidden_dim: int = Field(default=128, description="Hidden dimension of the LSTM")
    embedding_dim: int = Field(default=128, description="Dimension of the interaction embedding")


class DKTModel(nn.Module):
    def __init__(self, num_skills: int, hidden_dim: int = 128, embedding_dim: int = 128):
        super().__init__()
        self.num_skills = num_skills
        self.hidden_dim = hidden_dim
        
        # We embed the (skill_id, correctness) pair.
        # skill_id is in [0, num_skills - 1]
        # correctness is 0 or 1
        # Interaction ID can be encoded as skill_id + correctness * num_skills
        # This gives 2 * num_skills possible interactions.
        self.interaction_embed = nn.Embedding(2 * num_skills, embedding_dim)
        
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
        
        # Linear head maps the hidden state to a probability for each skill.
        self.out = nn.Linear(hidden_dim, num_skills)
        
    def forward(self, interactions: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for the DKT model.
        
        Args:
            interactions: Tensor of shape (batch_size, seq_len)
                          containing interaction IDs.
                          interaction_id = skill_id + correctness * num_skills
                          
        Returns:
            logits: Tensor of shape (batch_size, seq_len, num_skills)
                    containing the unnormalized logits predicting correctness
                    for the *next* time step.
        """
        x = self.interaction_embed(interactions)  # (batch_size, seq_len, embedding_dim)
        
        h, _ = self.lstm(x)  # (batch_size, seq_len, hidden_dim)
        
        logits = self.out(h)  # (batch_size, seq_len, num_skills)
        return logits


class DKTKnowledgeTracer:
    """
    Wrapper for using DKTModel for inference within the application.
    Maintains a candidate's hidden state context and handles skill mapping.
    """
    def __init__(self, model_path: str | None = None, num_skills: int = 100):
        self.params = DKTParams(num_skills=num_skills)
        self.model = DKTModel(
            num_skills=self.params.num_skills,
            hidden_dim=self.params.hidden_dim,
            embedding_dim=self.params.embedding_dim
        )
        self.model.eval()
        
        if model_path:
            self.model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
            
    def _encode_interaction(self, skill_index: int, is_correct: bool) -> int:
        return skill_index + (int(is_correct) * self.params.num_skills)
        
    def predict_next(self, interaction_sequence: list[tuple[int, bool]]) -> torch.Tensor:
        """
        Predicts the mastery probabilities for all skills for the next time step.
        
        Args:
            interaction_sequence: List of tuples (skill_index, is_correct)
            
        Returns:
            probabilities: Tensor of shape (num_skills,) with probabilities [0, 1]
        """
        if not interaction_sequence:
            # Return prior (e.g., 0.5) if no history
            return torch.full((self.params.num_skills,), 0.5)
            
        encoded = [self._encode_interaction(s, c) for s, c in interaction_sequence]
        
        with torch.no_grad():
            x = torch.tensor([encoded], dtype=torch.long)  # shape (1, seq_len)
            logits = self.model(x)  # shape (1, seq_len, num_skills)
            
            # We want the prediction after seeing the entire sequence
            final_logits = logits[0, -1, :]  # shape (num_skills,)
            probabilities = torch.sigmoid(final_logits)
            
        return probabilities
