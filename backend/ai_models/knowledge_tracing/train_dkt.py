import argparse
import logging
import random
from pathlib import Path

import torch
import torch.nn as nn
from torch.optim import Adam
from torch.utils.data import DataLoader, Dataset

from ai_models.knowledge_tracing.dkt import DKTModel
from app.core.logging import setup_logging

logger = logging.getLogger(__name__)

class SyntheticDKTDataset(Dataset):
    """
    Generates synthetic interaction sequences for training DKT.
    Each student interacts with a sequence of skills.
    Over time, they are more likely to answer correctly (learning).
    """
    def __init__(self, num_students: int = 1000, max_seq_len: int = 50, num_skills: int = 100):
        self.num_students = num_students
        self.max_seq_len = max_seq_len
        self.num_skills = num_skills
        self.data = self._generate_data()
        
    def _generate_data(self):
        data = []
        for _ in range(self.num_students):
            seq_len = random.randint(10, self.max_seq_len)
            sequence = []
            
            # Keep a rough "mastery" per skill, starts low
            mastery = {s: random.uniform(0.1, 0.4) for s in range(self.num_skills)}
            
            for _ in range(seq_len):
                skill = random.randint(0, self.num_skills - 1)
                
                # Probability of correct increases if they practice
                prob_correct = mastery[skill]
                is_correct = random.random() < prob_correct
                
                sequence.append((skill, is_correct))
                
                # Increase mastery
                mastery[skill] = min(0.95, mastery[skill] + 0.1)
                
            data.append(sequence)
        return data
        
    def __len__(self):
        return len(self.data)
        
    def __getitem__(self, idx):
        # We need input sequences (interactions) and target sequences (next correctness)
        # Sequence: [(s1, c1), (s2, c2), ..., (s_T, c_T)]
        # Input to model: [x1, x2, ..., x_T-1]
        # Target for next: c2, c3, ..., c_T
        # Target skill: s2, s3, ..., s_T
        
        seq = self.data[idx]
        
        # We encode x_t = skill_t + is_correct_t * num_skills
        interactions = [s + (1 if c else 0) * self.num_skills for s, c in seq[:-1]]
        
        target_skills = [s for s, c in seq[1:]]
        target_correct = [1.0 if c else 0.0 for s, c in seq[1:]]
        
        return (
            torch.tensor(interactions, dtype=torch.long),
            torch.tensor(target_skills, dtype=torch.long),
            torch.tensor(target_correct, dtype=torch.float32)
        )

def pad_collate(batch):
    """
    Pads sequences to the max length in the batch.
    """
    interactions, target_skills, target_correct = zip(*batch, strict=False)
    
    lengths = torch.tensor([len(x) for x in interactions])
    
    interactions_padded = nn.utils.rnn.pad_sequence(interactions, batch_first=True, padding_value=0)
    target_skills_padded = nn.utils.rnn.pad_sequence(target_skills, batch_first=True, padding_value=0)
    target_correct_padded = nn.utils.rnn.pad_sequence(target_correct, batch_first=True, padding_value=-1.0)
    
    return interactions_padded, target_skills_padded, target_correct_padded, lengths


def train_model(epochs: int, batch_size: int, num_skills: int, lr: float, save_path: str):
    logger.info("Generating synthetic data...")
    dataset = SyntheticDKTDataset(num_students=2000, max_seq_len=60, num_skills=num_skills)
    
    # Split into train/val
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=pad_collate)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, collate_fn=pad_collate)
    
    model = DKTModel(num_skills=num_skills, hidden_dim=64, embedding_dim=64)
    optimizer = Adam(model.parameters(), lr=lr)
    
    # Use BCEWithLogitsLoss
    criterion = nn.BCEWithLogitsLoss(reduction='none') 
    
    logger.info("Starting training...")
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        total_steps = 0
        
        for batch in train_loader:
            interactions, target_skills, target_correct, lengths = batch
            
            optimizer.zero_grad()
            logits = model(interactions)
            
            mask = target_correct != -1.0
            
            target_skills_expanded = target_skills.unsqueeze(-1) # (batch, seq, 1)
            predicted_logits = torch.gather(logits, 2, target_skills_expanded).squeeze(-1) # (batch, seq)
            
            # Compute loss only on valid mask
            loss = criterion(predicted_logits, target_correct)
            loss = (loss * mask).sum() / mask.sum()
            
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            total_steps += 1
            
        avg_train_loss = train_loss / total_steps
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_steps = 0
        with torch.no_grad():
            for batch in val_loader:
                interactions, target_skills, target_correct, lengths = batch
                logits = model(interactions)
                mask = target_correct != -1.0
                target_skills_expanded = target_skills.unsqueeze(-1)
                predicted_logits = torch.gather(logits, 2, target_skills_expanded).squeeze(-1)
                
                loss = criterion(predicted_logits, target_correct)
                loss = (loss * mask).sum() / mask.sum()
                val_loss += loss.item()
                val_steps += 1
                
        avg_val_loss = val_loss / val_steps
        logger.info(f"Epoch {epoch+1}/{epochs} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
        
    # Save the model
    save_dir = Path(save_path).parent
    save_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), save_path)
    logger.info(f"Model saved to {save_path}")

if __name__ == "__main__":
    setup_logging()
    parser = argparse.ArgumentParser(description="Train DKT Model")
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--num-skills", type=int, default=100, help="Number of unique skills")
    parser.add_argument("--lr", type=float, default=0.01, help="Learning rate")
    parser.add_argument("--save-path", type=str, default="checkpoints/dkt_model.pt", help="Path to save model")
    
    args = parser.parse_args()
    train_model(args.epochs, args.batch_size, args.num_skills, args.lr, args.save_path)
