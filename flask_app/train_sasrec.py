import numpy as np
import torch
import pickle
import time
import argparse
from torch.utils.data import Dataset, DataLoader, RandomSampler
from sasrec_model import SASRec

# --- CONFIGURATION (Tuned for RTX 4060) ---
class Args:
    batch_size = 128
    lr = 0.001
    maxlen = 200        # Maximum sequence length
    hidden_units = 128  # Dimension of embedding (Bigger = Smarter)
    num_blocks = 2      # Transformer Layers
    num_heads = 2       # Attention Heads
    dropout_rate = 0.2  # Prevents overfitting
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    num_epochs = 20     # More epochs for higher accuracy

args = Args()

# --- DATASET LOADER ---
class SASRecDataset(Dataset):
    def __init__(self, sequences, num_items):
        self.sequences = sequences
        self.num_items = num_items

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        # Strategy: Randomly mask one item to predict
        seq = self.sequences[idx]
        return torch.tensor(seq, dtype=torch.long) # Return raw sequence, process in batch

def get_batch_data(sequences, batch_indices, num_items):
    # Custom collator to generate negatives on the fly
    seqs = [sequences[i] for i in batch_indices]
    
    input_seqs = []
    pos_seqs = []
    neg_seqs = []
    
    for seq in seqs:
        # Truncate
        if len(seq) > args.maxlen: seq = seq[-args.maxlen:]
        
        # Pad
        pad_len = args.maxlen - len(seq)
        
        # INPUT: [0, 0, A, B] (Everything except last item)
        input_seq = [0]*pad_len + seq[:-1] 
        
        # POSITIVE TARGET: [0, 0, B, C] (Everything shifted by 1)
        pos_seq = [0]*pad_len + seq[1:]    
        
        # NEGATIVE TARGET: [0, 0, X, Y] (Random wrong movies)
        neg_seq = []
        ts = set(seq)
        for _ in range(len(pos_seq)):
            t = np.random.randint(1, num_items + 1)
            while t in ts:
                t = np.random.randint(1, num_items + 1)
            neg_seq.append(t)
            
        input_seqs.append(input_seq)
        pos_seqs.append(pos_seq)
        neg_seqs.append(neg_seq)
        
    return np.array(input_seqs), np.array(pos_seqs), np.array(neg_seqs)

# --- TRAINING LOOP ---
if __name__ == "__main__":
    print(f"Training SASRec on {args.device}...")
    
    # Load Data
    with open('processed_sequences.pkl', 'rb') as f:
        sequences = pickle.load(f)
    with open('item_encoder.pkl', 'rb') as f:
        item_encoder = pickle.load(f)
        
    num_items = len(item_encoder.classes_)
    print(f"Loaded {len(sequences)} sequences. Items: {num_items}")
    
    # Initialize Model
    model = SASRec(num_items, args).to(args.device)
    
    # Optimizer (Adam is standard for Transformers)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, betas=(0.9, 0.98))
    
    # Loss Function (Binary Cross Entropy)
    bce_criterion = torch.nn.BCEWithLogitsLoss()

    # Training
    num_batches = len(sequences) // args.batch_size
    
    for epoch in range(1, args.num_epochs + 1):
        model.train()
        total_loss = 0.0
        
        # Shuffle indices
        indices = np.arange(len(sequences))
        np.random.shuffle(indices)
        
        for i in range(num_batches):
            batch_idx = indices[i * args.batch_size : (i + 1) * args.batch_size]
            
            # Get Data
            # Note: We pass num_items to generate negatives correctly
            u_seq, pos, neg = get_batch_data(sequences, batch_idx, num_items)
            
            u_seq = torch.tensor(u_seq, dtype=torch.long).to(args.device)
            pos = torch.tensor(pos, dtype=torch.long).to(args.device)
            neg = torch.tensor(neg, dtype=torch.long).to(args.device)
            
            pos_logits, neg_logits = model(u_seq, pos, neg)
            
            # Calculate Loss 
            pos_labels = torch.ones(pos_logits.shape, device=args.device)
            neg_labels = torch.zeros(neg_logits.shape, device=args.device)
            
            # --- FIX IS HERE: USE PYTORCH MASKING, NOT NUMPY ---
            # Create a boolean mask where the target is NOT 0 (Padding)
            mask = (pos != 0) 
            
            # Apply the mask to ignore padding in the loss calculation
            # We only look at indices where mask is True
            loss = bce_criterion(pos_logits[mask], pos_labels[mask]) + \
                   bce_criterion(neg_logits[mask], neg_labels[mask])
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
            if i % 100 == 0:
                print(f"Epoch {epoch} | Batch {i}/{num_batches} | Loss: {loss.item():.4f}")
                
        print(f"--- Epoch {epoch} Complete. Avg Loss: {total_loss/num_batches:.4f} ---")
        
        # Save Model Every 5 Epochs
        if epoch % 5 == 0:
            torch.save(model.state_dict(), f"sasrec_epoch_{epoch}.pth")
            print("Model Saved.")