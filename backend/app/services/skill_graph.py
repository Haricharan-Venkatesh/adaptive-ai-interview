import logging
import os
import sys

import networkx as nx

from app.models.candidate import CandidateState, CompetencyNode, SkillEdge

# Add backend to path to allow importing ai_models if not already
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from ai_models.knowledge_tracing.bkt import BKTKnowledgeTracer

logger = logging.getLogger(__name__)

class SkillGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.tracer = BKTKnowledgeTracer()
        self._initialize_base_graph()

    def _initialize_base_graph(self):
        nodes = [
            CompetencyNode(skill_id="python_basics", name="Python Basics", category="Language"),
            CompetencyNode(skill_id="python_oop", name="Python OOP", category="Language"),
            CompetencyNode(skill_id="data_structures", name="Data Structures", category="DSA"),
            CompetencyNode(skill_id="algorithms", name="Algorithms", category="DSA"),
            CompetencyNode(skill_id="system_design", name="System Design", category="Architecture"),
        ]
        for node in nodes:
            self.graph.add_node(node.skill_id, data=node)

        edges = [
            SkillEdge(source_id="python_basics", target_id="python_oop", weight=1.0),
            SkillEdge(source_id="python_basics", target_id="data_structures", weight=0.8),
            SkillEdge(source_id="data_structures", target_id="algorithms", weight=1.0),
            SkillEdge(source_id="algorithms", target_id="system_design", weight=0.5),
        ]
        for edge in edges:
            self.graph.add_edge(edge.source_id, edge.target_id, weight=edge.weight)
            
        logger.info("Initialized base skill graph with %d nodes and %d edges", self.graph.number_of_nodes(), self.graph.number_of_edges())

    def get_node(self, skill_id: str) -> CompetencyNode | None:
        if skill_id in self.graph:
            return self.graph.nodes[skill_id]["data"]
        return None

    def get_prerequisites(self, skill_id: str) -> list[CompetencyNode]:
        if skill_id not in self.graph:
            return []
        preds = self.graph.predecessors(skill_id)
        return [self.graph.nodes[p]["data"] for p in preds]

    def get_dependent_skills(self, skill_id: str) -> list[CompetencyNode]:
        if skill_id not in self.graph:
            return []
        succs = self.graph.successors(skill_id)
        return [self.graph.nodes[s]["data"] for s in succs]
        
    def initialize_candidate_state(self, session_id: str) -> CandidateState:
        state = CandidateState(session_id=session_id)
        for node_id, data in self.graph.nodes(data=True):
            node_copy = data["data"].model_copy()
            # Initialize mastery probability with the BKT prior (p_l0)
            node_copy.mastery_probability = self.tracer.get_params(node_id).p_l0
            state.skills[node_id] = node_copy
        return state

    def update_skill(self, candidate_state: CandidateState, skill_id: str, is_correct: bool, confidence_increment: float = 0.1) -> CandidateState:
        if skill_id not in candidate_state.skills:
            return candidate_state
            
        node = candidate_state.skills[skill_id]
        node.questions_attempted += 1
        if is_correct:
            node.questions_correct += 1
            
        # BKT Update
        node.mastery_probability = self.tracer.update(skill_id, node.mastery_probability, is_correct)
            
        node.confidence = min(1.0, node.confidence + confidence_increment)
        
        if is_correct:
            for dep_node in self.get_dependent_skills(skill_id):
                if dep_node.skill_id in candidate_state.skills:
                    candidate_dep = candidate_state.skills[dep_node.skill_id]
                    candidate_dep.mastery_probability = min(1.0, candidate_dep.mastery_probability + 0.05)

        return candidate_state

skill_graph_service = SkillGraph()
