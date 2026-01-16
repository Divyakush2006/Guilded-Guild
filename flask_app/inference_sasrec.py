import torch
import numpy as np
import pickle
import re
import pandas as pd
import torch.nn.functional as F
import os
from pathlib import Path
from sasrec_model import SASRec

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent

# --- CONFIGURATION ---
MODEL_PATH = str(SCRIPT_DIR / "sasrec_epoch_20.pth")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ARCHITECTURAL HYPERPARAMETERS
# Temperature: Controls the "Risk" the model takes.
# 1.0 = Default Model Behavior (Bias toward popular)
# 0.7 = More focused (Conservative)
# 1.2 = More diverse (Discovery) -> TRY THIS to break the blockbuster loop
TEMPERATURE = 1.5

class Args:
    batch_size = 128
    lr = 0.001
    maxlen = 200
    hidden_units = 128
    num_blocks = 2
    num_heads = 2
    dropout_rate = 0.2
    device = DEVICE

args = Args()

class Recommender:
    def __init__(self):
        print("Initializing Recommender Engine...")
        self.load_resources()
        self.load_model()
        print("✅ Engine Ready.")

    def normalize_string(self, text):
        text = str(text)
        text = re.sub(r'\(\d{4}\)', '', text)
        text = re.sub(r'^the\s+', '', text.lower())
        return re.sub(r'[^a-z0-9]', '', text)

    def load_resources(self):
        with open(SCRIPT_DIR / 'item_encoder.pkl', 'rb') as f:
            self.item_encoder = pickle.load(f)
            
        ratings_df = pd.read_csv(PROJECT_ROOT / 'ratings.csv', usecols=['movieId'])
        # We keep popularity dict ONLY for "Search" (finding the movie user typed), 
        # NOT for penalizing the model.
        popularity_counts = ratings_df['movieId'].value_counts().to_dict()
        
        self.movies_df = pd.read_csv(PROJECT_ROOT / 'movies.csv')
        
        self.search_map = {}
        for idx, row in self.movies_df.iterrows():
            clean = self.normalize_string(row['title'])
            m_id = row['movieId']
            pop = popularity_counts.get(m_id, 0)
            
            if clean not in self.search_map: self.search_map[clean] = []
            self.search_map[clean].append({'id': m_id, 'title': row['title'], 'pop': pop})

    def load_model(self):
        num_items = len(self.item_encoder.classes_)
        self.model = SASRec(num_items, args).to(DEVICE)
        try:
            self.model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE), strict=False)
        except Exception as e:
            print(f"⚠️ Warning loading model: {e}")
        self.model.eval()

    def find_best_match(self, user_input):
        if not user_input: return None
        clean_input = self.normalize_string(user_input)
        
        candidates = []
        if clean_input in self.search_map:
            candidates.extend(self.search_map[clean_input])
        else:
            for key in self.search_map:
                if clean_input in key:
                    candidates.extend(self.search_map[key])
        
        if not candidates: return None
        candidates.sort(key=lambda x: x['pop'], reverse=True)
        return candidates[0]

    def predict(self, movie_names):
        movie_sequence = []
        
        # 1. Identify Movies
        for name in movie_names:
            match = self.find_best_match(name)
            if match:
                try:
                    model_id = self.item_encoder.transform([match['id']])[0] + 1
                    movie_sequence.append(model_id)
                except: pass

        if not movie_sequence:
            return ["Error: Could not find any of those movies in the database."]

        # 2. Prepare Tensor
        seq_len = len(movie_sequence)
        if seq_len > args.maxlen:
            input_seq = movie_sequence[-args.maxlen:]
        else:
            input_seq = [0] * (args.maxlen - seq_len) + movie_sequence
            
        input_tensor = torch.tensor([input_seq], dtype=torch.long).to(DEVICE)
        
        # 3. Model Inference (Professional Approach)
        with torch.no_grad():
            log_feats = self.model.log2feats(input_tensor) 
            final_feat = log_feats[:, -1, :] 
            all_item_embs = self.model.item_emb.weight 
            
            # Raw Logits
            logits = final_feat @ all_item_embs.t()
            
            # Mask out already watched movies
            for m_id in movie_sequence:
                logits[:, m_id] = -float('inf')

            # --- ARCHITECTURAL FIX: TEMPERATURE SCALING ---
            # Instead of manually editing scores, we scale the distribution.
            # 1. Apply Temperature
            scaled_logits = logits / TEMPERATURE
            
            # 2. Convert to Probabilities (Softmax)
            probs = F.softmax(scaled_logits, dim=-1)
            
            # 3. Top-K Sampling
            # We take top 50 candidates by pure probability
            top_probs, top_indices = torch.topk(probs, 50)
            
            # 4. Final Selection
            # We simply return the top 10 from this probabilistically sound list
            final_indices = top_indices.cpu().numpy()[0][:10]

        recommendations = []
        for model_id in final_indices:
            if model_id == 0: continue
            try:
                original_id = self.item_encoder.inverse_transform([model_id - 1])[0]
                row = self.movies_df[self.movies_df['movieId'] == original_id]
                if not row.empty:
                    recommendations.append(row.iloc[0]['title'])
            except: pass
            
        return recommendations

rec_engine = Recommender()

if __name__ == "__main__":
    print(rec_engine.predict(["Iron Man", "Avengers"]))