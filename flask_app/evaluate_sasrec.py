import torch
import torch.nn as nn
import numpy as np
import pickle
from tqdm import tqdm
from sklearn.metrics import roc_auc_score

# ==========================================
# 1. YOUR MODEL DEFINITION (Copied from SASREC_MODEL.PY)
# ==========================================

class PointWiseFeedForward(nn.Module):
    def __init__(self, hidden_units, dropout_rate):
        super(PointWiseFeedForward, self).__init__()
        self.conv1 = nn.Conv1d(hidden_units, hidden_units, kernel_size=1)
        self.dropout1 = nn.Dropout(p=dropout_rate)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv1d(hidden_units, hidden_units, kernel_size=1)
        self.dropout2 = nn.Dropout(p=dropout_rate)

    def forward(self, inputs):
        outputs = self.dropout2(self.conv2(self.relu(self.dropout1(self.conv1(inputs.transpose(-1, -2))))))
        return outputs.transpose(-1, -2) + inputs 

class SASRec(nn.Module):
    def __init__(self, item_num, args):
        super(SASRec, self).__init__()
        self.item_num = item_num
        self.dev = args.device

        # 1. EMBEDDINGS
        self.item_emb = nn.Embedding(self.item_num + 1, args.hidden_units, padding_idx=0)
        self.pos_emb = nn.Embedding(args.maxlen, args.hidden_units) 
        self.emb_dropout = nn.Dropout(p=args.dropout_rate)

        # 2. ATTENTION BLOCKS
        self.attention_layernorms = nn.ModuleList() 
        self.attention_layers = nn.ModuleList()
        self.forward_layernorms = nn.ModuleList()
        self.forward_layers = nn.ModuleList()

        self.last_layernorm = nn.LayerNorm(args.hidden_units, eps=1e-8)

        for _ in range(args.num_blocks):
            new_attn_layernorm = nn.LayerNorm(args.hidden_units, eps=1e-8)
            self.attention_layernorms.append(new_attn_layernorm)

            new_attn_layer = nn.MultiheadAttention(args.hidden_units, args.num_heads, args.dropout_rate)
            self.attention_layers.append(new_attn_layer)

            new_fwd_layernorm = nn.LayerNorm(args.hidden_units, eps=1e-8)
            self.forward_layernorms.append(new_fwd_layernorm)

            new_fwd_layer = PointWiseFeedForward(args.hidden_units, args.dropout_rate)
            self.forward_layers.append(new_fwd_layer)

    def log2feats(self, log_seqs):
        seqs = self.item_emb(log_seqs)
        seqs *= self.item_emb.embedding_dim ** 0.5
        
        positions = np.tile(np.array(range(log_seqs.shape[1])), [log_seqs.shape[0], 1])
        seqs += self.pos_emb(torch.tensor(positions, dtype=torch.long, device=self.dev))
        seqs = self.emb_dropout(seqs)

        timeline_mask = (log_seqs == 0) 
        seqs *= ~timeline_mask.unsqueeze(-1) 

        tl = seqs.shape[1] 
        attention_mask = ~torch.tril(torch.ones((tl, tl), dtype=torch.bool, device=self.dev))

        for i in range(len(self.attention_layers)):
            Q = self.attention_layernorms[i](seqs)
            mha_outputs, _ = self.attention_layers[i](Q.transpose(0, 1), Q.transpose(0, 1), Q.transpose(0, 1), attn_mask=attention_mask)
            seqs = Q + mha_outputs.transpose(0, 1)

            seqs = self.forward_layernorms[i](seqs)
            seqs = self.forward_layers[i](seqs)
            seqs *= ~timeline_mask.unsqueeze(-1)

        log_feats = self.last_layernorm(seqs)
        return log_feats

    # Added for Evaluation: A method to predict scores for specific candidates
    def predict(self, seqs, item_indices):
        log_feats = self.log2feats(seqs) 
        final_feat = log_feats[:, -1, :] # Only take the last step
        
        item_embs = self.item_emb(torch.LongTensor(item_indices).to(self.dev)) # [num_candidates, H]
        
        logits = final_feat.matmul(item_embs.t()) # [1, num_candidates]
        return logits

# ==========================================
# 2. CONFIGURATION & ARGS CLASS
# ==========================================
MODEL_PATH = "sasrec_epoch_20.pth"
DATA_PATH = "processed_sequences.pkl"
ENCODER_PATH = "item_encoder.pkl"
TOP_K = 10
NUM_NEGATIVES = 100
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# This mimics the 'parser' arguments you likely used during training
class Args:
    def __init__(self):
        self.batch_size = 128
        self.lr = 0.001
        self.maxlen = 200
        self.hidden_units = 128  # <--- IF ERROR, TRY 64 or 50
        self.num_blocks = 2
        self.num_heads = 2       # <--- IF ERROR, TRY 1 or 4
        self.dropout_rate = 0.2
        self.device = DEVICE

# ==========================================
# 3. EVALUATION LOGIC
# ==========================================
def load_data():
    print(f"Loading data from {DATA_PATH}...")
    with open(DATA_PATH, 'rb') as f:
        sequences = pickle.load(f)
    with open(ENCODER_PATH, 'rb') as f:
        item_encoder = pickle.load(f)
        num_items = len(item_encoder.classes_)
    return sequences, num_items

def get_negative_samples(target_item, num_items, num_negatives, input_set):
    negatives = []
    while len(negatives) < num_negatives:
        neg_id = np.random.randint(1, num_items)
        if neg_id != target_item and neg_id not in input_set:
            negatives.append(neg_id)
    return negatives

if __name__ == "__main__":
    sequences, num_items = load_data()
    args = Args()
    
    # Initialize Model
    model = SASRec(num_items, args).to(DEVICE)
    
    # Load Weights
    print(f"Loading weights from {MODEL_PATH}...")
    try:
        model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    except RuntimeError as e:
        print("\n❌ SIZE MISMATCH ERROR")
        print("Your saved model params don't match the Args class above.")
        print("Check 'hidden_units', 'num_blocks', or 'num_heads' in the Args class.")
        print(e)
        exit()

    model.eval()
    
    auc_scores, hit_rates, ndcg_scores = [], [], []
    
    print(f"Evaluating (Top-{TOP_K})...")
    with torch.no_grad():
        for seq in tqdm(sequences): 
            if len(seq) < 2: continue
            
            target_item = seq[-1]
            input_seq = seq[:-1]
            
            # Truncate or Pad to maxlen
            input_seq = input_seq[-args.maxlen:]
            pad_len = args.maxlen - len(input_seq)
            input_seq = [0] * pad_len + input_seq
            
            seq_tensor = torch.LongTensor([input_seq]).to(DEVICE)
            
            # Get Negatives
            negatives = get_negative_samples(target_item, num_items, NUM_NEGATIVES, set(seq))
            candidates = [target_item] + negatives
            
            # Predict
            # We use the new .predict() method to score only our 101 candidates
            scores = model.predict(seq_tensor, candidates).cpu().numpy()[0]
            
            # METRICS
            # 1. AUC (Target vs Negatives)
            y_true = np.zeros(len(candidates))
            y_true[0] = 1
            try:
                auc_scores.append(roc_auc_score(y_true, scores))
            except: pass

            # 2. Ranking (Hit Rate & NDCG)
            # Sort descending (highest score first)
            ranked_indices = np.argsort(-scores)
            
            # Check if index 0 (Target) is in top K
            top_k = ranked_indices[:TOP_K]
            
            if 0 in top_k:
                hit_rates.append(1)
                rank = np.where(top_k == 0)[0][0] + 1
                ndcg_scores.append(1.0 / np.log2(rank + 1))
            else:
                hit_rates.append(0)
                ndcg_scores.append(0)

    print("\n" + "="*30)
    print(f"RESULTS FOR {MODEL_PATH}")
    print("="*30)
    print(f"AUC:      {np.mean(auc_scores):.4f}")
    print(f"Hit Rate: {np.mean(hit_rates):.4f}")
    print(f"NDCG:     {np.mean(ndcg_scores):.4f}")
    print("="*30)