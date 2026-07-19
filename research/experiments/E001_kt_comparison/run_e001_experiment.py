import sys
import os
import random
import logging

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend")))

from sklearn.metrics import roc_auc_score

from app.core.logging import setup_logging
from ai_models.knowledge_tracing.factory import KnowledgeTracerFactory

logger = logging.getLogger(__name__)

def generate_synthetic_evaluation_data(num_students=500, max_seq_len=20, num_skills=20):
    """
    Generates synthetic sequences.
    For each sequence, we want to predict the correctness of the last interaction
    given all previous interactions.
    """
    data = []
    for _ in range(num_students):
        seq_len = random.randint(5, max_seq_len)
        sequence = []
        mastery = {s: random.uniform(0.1, 0.4) for s in range(num_skills)}
        
        for _ in range(seq_len):
            skill = random.randint(0, num_skills - 1)
            prob_correct = mastery[skill]
            is_correct = random.random() < prob_correct
            sequence.append((skill, is_correct))
            mastery[skill] = min(0.95, mastery[skill] + 0.15)
            
        data.append(sequence)
    return data

def run_experiment():
    setup_logging()
    num_skills = 20
    
    logger.info("Generating synthetic evaluation data...")
    test_data = generate_synthetic_evaluation_data(num_students=1000, max_seq_len=30, num_skills=num_skills)
    
    # We will test BKT and DKT
    bkt = KnowledgeTracerFactory.create("bkt", num_skills=num_skills)
    
    # DKT will be randomly initialized since we didn't provide a checkpoint path.
    # In a real evaluation, we would provide the path to a fully trained model.
    dkt = KnowledgeTracerFactory.create("dkt", num_skills=num_skills)
    
    bkt_preds = []
    dkt_preds = []
    targets = []
    
    logger.info("Running inference...")
    for seq in test_data:
        # Predict the last interaction given the history
        history = seq[:-1]
        target_skill, target_correct = seq[-1]
        
        bkt_probs = bkt.predict_next(history)
        dkt_probs = dkt.predict_next(history)
        
        bkt_preds.append(bkt_probs[target_skill])
        dkt_preds.append(dkt_probs[target_skill])
        targets.append(1 if target_correct else 0)
        
    logger.info("Computing metrics...")
    bkt_auc = roc_auc_score(targets, bkt_preds)
    dkt_auc = roc_auc_score(targets, dkt_preds)
    
    print("\n" + "="*40)
    print("Experiment E001 Results:")
    print(f"BKT AUC: {bkt_auc:.4f}")
    print(f"DKT AUC: {dkt_auc:.4f}")
    print("="*40 + "\n")

if __name__ == "__main__":
    run_experiment()
