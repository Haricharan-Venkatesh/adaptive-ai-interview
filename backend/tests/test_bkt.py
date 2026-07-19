import pytest
from ai_models.knowledge_tracing.bkt import BKTParams, BKTModel, BKTKnowledgeTracer

def test_bkt_params_default():
    params = BKTParams()
    assert params.p_L0 == 0.1
    assert params.p_T == 0.1
    assert params.p_G == 0.2
    assert params.p_S == 0.1

def test_bkt_model_update_correct():
    params = BKTParams(p_L0=0.1, p_T=0.1, p_G=0.2, p_S=0.1)
    model = BKTModel(params)
    
    # Update on correct answer
    p_L_next = model.update(params.p_L0, is_correct=True)
    
    # Should increase mastery probability
    assert p_L_next > params.p_L0

def test_bkt_model_update_incorrect():
    params = BKTParams(p_L0=0.5, p_T=0.1, p_G=0.2, p_S=0.1)
    model = BKTModel(params)
    
    # Update on incorrect answer
    p_L_next = model.update(0.5, is_correct=False)
    
    # Should decrease mastery probability
    assert p_L_next < 0.5

def test_bkt_model_predict():
    params = BKTParams(p_S=0.1, p_G=0.2)
    model = BKTModel(params)
    
    # Predict with 0 mastery (should be pure guess)
    assert model.predict(0.0) == 0.2
    
    # Predict with 1.0 mastery (should be 1 - slip)
    assert model.predict(1.0) == 0.9
    
    # Predict with 0.5 mastery
    assert model.predict(0.5) == 0.55

def test_bkt_knowledge_tracer():
    skill_params = {
        "hard_skill": BKTParams(p_L0=0.05, p_T=0.05, p_G=0.1, p_S=0.2)
    }
    tracer = BKTKnowledgeTracer(skill_params=skill_params)
    
    # Check default params
    default = tracer.get_params("unknown_skill")
    assert default.p_L0 == 0.1
    
    # Check custom params
    hard = tracer.get_params("hard_skill")
    assert hard.p_L0 == 0.05
    
    # Test update via tracer
    updated = tracer.update("hard_skill", 0.05, is_correct=True)
    assert updated > 0.05
