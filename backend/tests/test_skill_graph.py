import pytest

from app.services.skill_graph import SkillGraph


@pytest.fixture
def skill_graph():
    return SkillGraph()

def test_graph_initialization(skill_graph):
    assert skill_graph.graph.number_of_nodes() > 0
    assert skill_graph.graph.number_of_edges() > 0
    
    node = skill_graph.get_node("python_basics")
    assert node is not None
    assert node.name == "Python Basics"

def test_prerequisites(skill_graph):
    prereqs = skill_graph.get_prerequisites("python_oop")
    assert any(p.skill_id == "python_basics" for p in prereqs)
    
def test_candidate_state_init(skill_graph):
    state = skill_graph.initialize_candidate_state("session_123")
    assert state.session_id == "session_123"
    assert "python_basics" in state.skills
    assert state.skills["python_basics"].mastery_probability == 0.1

def test_update_skill_correct(skill_graph):
    state = skill_graph.initialize_candidate_state("session_123")
    initial_mastery = state.skills["python_basics"].mastery_probability
    
    state = skill_graph.update_skill(state, "python_basics", is_correct=True)
    
    assert state.skills["python_basics"].questions_attempted == 1
    assert state.skills["python_basics"].questions_correct == 1
    assert state.skills["python_basics"].mastery_probability > initial_mastery

def test_update_skill_incorrect(skill_graph):
    state = skill_graph.initialize_candidate_state("session_123")
    state.skills["python_basics"].mastery_probability = 0.5
    
    state = skill_graph.update_skill(state, "python_basics", is_correct=False)
    
    assert state.skills["python_basics"].questions_attempted == 1
    assert state.skills["python_basics"].questions_correct == 0
    assert state.skills["python_basics"].mastery_probability < 0.5
