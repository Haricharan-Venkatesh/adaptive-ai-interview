import pytest

from ai_models.knowledge_tracing.factory import (
    BKTAdapter,
    DKTAdapter,
    DKTGNNAdapter,
    KnowledgeTracerFactory,
)
from ai_models.knowledge_tracing.gnn import HAS_PYG


def test_knowledge_tracer_factory_bkt():
    adapter = KnowledgeTracerFactory.create("bkt", num_skills=5)
    assert isinstance(adapter, BKTAdapter)
    
    probs = adapter.predict_next([(0, True), (1, False)])
    assert probs.shape == (5,)
    assert (probs >= 0).all() and (probs <= 1).all()

def test_knowledge_tracer_factory_dkt():
    adapter = KnowledgeTracerFactory.create("dkt", num_skills=5)
    assert isinstance(adapter, DKTAdapter)
    
    probs = adapter.predict_next([(0, True), (1, False)])
    assert probs.shape == (5,)
    assert (probs >= 0).all() and (probs <= 1).all()

@pytest.mark.skipif(not HAS_PYG, reason="torch-geometric is not installed")
def test_knowledge_tracer_factory_dkt_gnn():
    edges = [[0, 1], [1, 2]]
    adapter = KnowledgeTracerFactory.create("dkt_gnn", num_skills=5, edges=edges)
    assert isinstance(adapter, DKTGNNAdapter)
    
    probs = adapter.predict_next([(0, True), (1, False)])
    assert probs.shape == (5,)
    assert (probs >= 0).all() and (probs <= 1).all()

def test_knowledge_tracer_factory_invalid():
    with pytest.raises(ValueError):
        KnowledgeTracerFactory.create("invalid_model", num_skills=5)
