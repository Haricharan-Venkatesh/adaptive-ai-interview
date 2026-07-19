import logging

import numpy as np

from ai_models.knowledge_tracing.bkt import BKTKnowledgeTracer
from ai_models.knowledge_tracing.dkt import DKTKnowledgeTracer
from ai_models.knowledge_tracing.gnn import GNNKnowledgePropagator

logger = logging.getLogger(__name__)

class KnowledgeTracerAdapter:
    """
    Unified interface for all knowledge tracing models.
    """
    def predict_next(self, interaction_sequence: list[tuple[int, bool]]) -> np.ndarray:
        """
        Returns a probability distribution of mastery across all skills.
        
        Args:
            interaction_sequence: List of (skill_id, is_correct)
            
        Returns:
            np.ndarray of shape (num_skills,) containing probabilities [0, 1]
        """
        raise NotImplementedError


class BKTAdapter(KnowledgeTracerAdapter):
    def __init__(self, num_skills: int):
        self.num_skills = num_skills
        self.tracer = BKTKnowledgeTracer()
        
    def predict_next(self, interaction_sequence: list[tuple[int, bool]]) -> np.ndarray:
        # BKT maintains state per skill.
        # We need to simulate the sequence from scratch if we don't have persistent state,
        # or we just replay it.
        self.tracer = BKTKnowledgeTracer()
        for _, _ in interaction_sequence:
            # We don't have current mastery cached here, we should just use the default prior
            # Wait, BKTKnowledgeTracer.update requires current_mastery!
            # Let's manage the mastery state directly in the adapter.
            pass
        
        # Actually, let's implement a clean simulation for BKT
        masteries = {str(i): self.tracer.get_params(str(i)).p_l0 for i in range(self.num_skills)}
        for skill_id, is_correct in interaction_sequence:
            sid = str(skill_id)
            masteries[sid] = self.tracer.update(sid, masteries[sid], is_correct)
            
        probs = [self.tracer.predict(str(i), masteries[str(i)]) for i in range(self.num_skills)]
        return np.array(probs)


class DKTAdapter(KnowledgeTracerAdapter):
    def __init__(self, num_skills: int, model_path: str | None = None):
        self.tracer = DKTKnowledgeTracer(model_path=model_path, num_skills=num_skills)
        
    def predict_next(self, interaction_sequence: list[tuple[int, bool]]) -> np.ndarray:
        probs = self.tracer.predict_next(interaction_sequence)
        return probs.detach().cpu().numpy()


class DKTGNNAdapter(KnowledgeTracerAdapter):
    def __init__(self, num_skills: int, dkt_path: str | None = None, gnn_path: str | None = None, edges: list[list[int]] | None = None):
        self.dkt = DKTKnowledgeTracer(model_path=dkt_path, num_skills=num_skills)
        self.gnn = GNNKnowledgePropagator(model_path=gnn_path, num_skills=num_skills)
        self.edges = edges if edges is not None else []
        
    def predict_next(self, interaction_sequence: list[tuple[int, bool]]) -> np.ndarray:
        # 1. Get temporal estimate from DKT
        dkt_probs = self.dkt.predict_next(interaction_sequence).detach().cpu().numpy().tolist()
        
        # 2. Propagate through graph
        gnn_outputs = self.gnn.propagate(dkt_probs, self.edges)
        
        return gnn_outputs["mastery_probs"].squeeze(-1).detach().cpu().numpy()


class KnowledgeTracerFactory:
    """
    Factory to instantiate the appropriate Knowledge Tracer based on configuration.
    """
    @staticmethod
    def create(model_type: str, num_skills: int, **kwargs) -> KnowledgeTracerAdapter:
        model_type = model_type.lower()
        if model_type == "bkt":
            logger.info("Initializing BKT Knowledge Tracer")
            return BKTAdapter(num_skills=num_skills)
        elif model_type == "dkt":
            logger.info("Initializing DKT Knowledge Tracer")
            return DKTAdapter(num_skills=num_skills, model_path=kwargs.get("dkt_path"))
        elif model_type == "dkt_gnn":
            logger.info("Initializing DKT+GNN Knowledge Tracer")
            return DKTGNNAdapter(
                num_skills=num_skills, 
                dkt_path=kwargs.get("dkt_path"), 
                gnn_path=kwargs.get("gnn_path"),
                edges=kwargs.get("edges")
            )
        else:
            raise ValueError(f"Unknown knowledge tracer model type: {model_type}")
