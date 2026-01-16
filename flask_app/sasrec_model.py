import torch
import torch.nn as nn
import numpy as np

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
        return outputs.transpose(-1, -2) + inputs # Residual Connection

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
        # FIX 1: log_seqs is already a Tensor on GPU. Don't wrap it in torch.LongTensor().
        seqs = self.item_emb(log_seqs)
        seqs *= self.item_emb.embedding_dim ** 0.5
        
        # Positions are created from scratch, so we convert them safely
        positions = np.tile(np.array(range(log_seqs.shape[1])), [log_seqs.shape[0], 1])
        seqs += self.pos_emb(torch.tensor(positions, dtype=torch.long, device=self.dev))
        seqs = self.emb_dropout(seqs)

        # Causality Mask
        timeline_mask = (log_seqs == 0) # Boolean mask for padding
        seqs *= ~timeline_mask.unsqueeze(-1) 

        # Attention Mask
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

    def forward(self, user_seqs, pos_seqs, neg_seqs):
        # 1. Get Context
        log_feats = self.log2feats(user_seqs) 

        # FIX 2: pos_seqs and neg_seqs are already on GPU. Just use them.
        pos_embs = self.item_emb(pos_seqs)
        neg_embs = self.item_emb(neg_seqs)

        # 3. Calculate Scores
        pos_logits = (log_feats * pos_embs).sum(dim=-1)
        neg_logits = (log_feats * neg_embs).sum(dim=-1)

        return pos_logits, neg_logits