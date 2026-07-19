import torch

from ai_models.knowledge_tracing.dkt import DKTKnowledgeTracer, DKTModel, DKTParams


def test_dkt_params():
    params = DKTParams(num_skills=50)
    assert params.num_skills == 50
    assert params.hidden_dim == 128

def test_dkt_model_forward():
    num_skills = 10
    model = DKTModel(num_skills=num_skills, hidden_dim=16, embedding_dim=16)
    
    # Batch of 2 students, sequence of 5 interactions
    batch_size = 2
    seq_len = 5
    
    # Interactions are indices in [0, 2 * num_skills - 1]
    # For example, skill 3 correct -> 3 + 10 = 13
    interactions = torch.tensor([
        [13, 2, 11, 4, 15],  # Student 1
        [1, 12, 13, 14, 5]   # Student 2
    ], dtype=torch.long)
    
    logits = model(interactions)
    
    # Output shape should be (batch_size, seq_len, num_skills)
    assert logits.shape == (batch_size, seq_len, num_skills)
    
    # The output is raw logits, not probabilities
    assert torch.isfinite(logits).all()

def test_dkt_knowledge_tracer_wrapper():
    num_skills = 20
    tracer = DKTKnowledgeTracer(num_skills=num_skills)
    
    # 1. Test empty sequence returns prior 0.5
    probs_empty = tracer.predict_next([])
    assert probs_empty.shape == (num_skills,)
    assert torch.all(probs_empty == 0.5)
    
    # 2. Test encoding logic
    # skill 5, correct
    encoded = tracer._encode_interaction(5, True)
    assert encoded == 5 + num_skills
    
    # skill 7, incorrect
    encoded = tracer._encode_interaction(7, False)
    assert encoded == 7
    
    # 3. Test prediction with sequence
    sequence = [(5, True), (7, False), (5, True)]
    probs = tracer.predict_next(sequence)
    
    assert probs.shape == (num_skills,)
    # Probabilities should be between 0 and 1
    assert torch.all(probs >= 0.0) and torch.all(probs <= 1.0)
