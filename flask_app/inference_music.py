"""
Music Recommendation Inference Engine
Uses SASRec model to predict next tracks based on listening history.
Mirrors the structure of inference_sasrec.py but for music.
"""

import torch
import numpy as np
import pickle
import re
import pandas as pd
import torch.nn.functional as F
from sasrec_model import SASRec
import requests

# --- CONFIGURATION ---
# For now, we'll use the same SASRec architecture
# Later we can train a music-specific model
MODEL_PATH = "sasrec_music.pth"  # Will be trained later
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TEMPERATURE = 1.5  # Diversity parameter

class Args:
    batch_size = 128
    lr = 0.001
    maxlen = 50  # Shorter sequence for music (more frequent changes)
    hidden_units = 128
    num_blocks = 2
    num_heads = 2
    dropout_rate = 0.2
    device = DEVICE

args = Args()

class MusicRecommender:
    def __init__(self, use_fallback=True):
        """
        Initialize Music Recommender
        
        Args:
            use_fallback: If True and no trained model exists, use Audius API directly
        """
        print("🎵 Initializing Music Recommender...")
        self.load_resources()
        self.use_fallback = use_fallback
        
        try:
            self.load_model()
            self.model_loaded = True
            print("✅ Model loaded successfully")
        except FileNotFoundError:
            self.model_loaded = False
            if use_fallback:
                print("⚠️ No trained model found - using Audius API fallback")
            else:
                raise
        
        print("✅ Music Recommender Ready")
    
    def normalize_string(self, text):
        """Normalize track/artist names for fuzzy matching"""
        text = str(text).lower()
        # Remove featured artists, remove special chars
        text = re.sub(r'\(feat\..*?\)', '', text)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return text.strip()
    
    def load_resources(self):
        """Load music dataset and encoders"""
        try:
            # Load dataset
            self.music_df = pd.read_pickle('music_dataset.pkl')
            
            # Load encoders
            with open('track_encoder.pkl', 'rb') as f:
                self.track_encoder = pickle.load(f)
            
            with open('artist_encoder.pkl', 'rb') as f:
                self.artist_encoder = pickle.load(f)
            
            # Create fuzzy search map
            self.search_map = {}
            for idx, row in self.music_df.iterrows():
                clean = self.normalize_string(row['title'])
                track_id = row['track_id']
                
                if clean not in self.search_map:
                    self.search_map[clean] = []
                
                self.search_map[clean].append({
                    'id': track_id,
                    'title': row['title'],
                    'artist': row['artist'],
                    'genre': row['genre'],
                    'play_count': row['play_count'],
                    'artwork_url': row['artwork_url'],
                    'stream_url': row['stream_url'],
                    'permalink': row['permalink']
                })
            
            print(f"📚 Loaded {len(self.music_df)} tracks")
            
        except FileNotFoundError as e:
            print(f"❌ Error loading resources: {e}")
            print("💡 Run 'python music_data_fetcher.py' first to build the dataset")
            raise
    
    def load_model(self):
        """Load trained SASRec model for music"""
        num_items = len(self.track_encoder.classes_)
        self.model = SASRec(num_items, args).to(DEVICE)
        
        try:
            self.model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE), strict=False)
            self.model.eval()
        except FileNotFoundError:
            raise FileNotFoundError(f"Model file {MODEL_PATH} not found")
    
    def find_best_match(self, user_input):
        """Fuzzy search for track name"""
        if not user_input:
            return None
        
        clean_input = self.normalize_string(user_input)
        
        # Exact match
        if clean_input in self.search_map:
            candidates = self.search_map[clean_input]
            # Sort by popularity
            candidates.sort(key=lambda x: x['play_count'], reverse=True)
            return candidates[0]
        
        # Partial match
        candidates = []
        for key in self.search_map:
            if clean_input in key or key in clean_input:
                candidates.extend(self.search_map[key])
        
        if candidates:
            candidates.sort(key=lambda x: x['play_count'], reverse=True)
            return candidates[0]
        
        return None
    
    def predict_with_model(self, track_names):
        """Use SASRec model for predictions"""
        track_sequence = []
        
        # 1. Identify tracks
        for name in track_names:
            match = self.find_best_match(name)
            if match:
                try:
                    model_id = self.track_encoder.transform([match['id']])[0] + 1
                    track_sequence.append(model_id)
                except:
                    pass
        
        if not track_sequence:
            return []
        
        # 2. Prepare tensor
        seq_len = len(track_sequence)
        if seq_len > args.maxlen:
            input_seq = track_sequence[-args.maxlen:]
        else:
            input_seq = [0] * (args.maxlen - seq_len) + track_sequence
        
        input_tensor = torch.tensor([input_seq], dtype=torch.long).to(DEVICE)
        
        # 3. Model inference
        with torch.no_grad():
            log_feats = self.model.log2feats(input_tensor)
            final_feat = log_feats[:, -1, :]
            all_item_embs = self.model.item_emb.weight
            
            logits = final_feat @ all_item_embs.t()
            
            # Mask watched tracks
            for track_id in track_sequence:
                logits[:, track_id] = -float('inf')
            
            # Temperature scaling
            scaled_logits = logits / TEMPERATURE
            probs = F.softmax(scaled_logits, dim=-1)
            
            # Top-K sampling
            top_probs, top_indices = torch.topk(probs, 20)
            final_indices = top_indices.cpu().numpy()[0][:10]
        
        # 4. Get track info
        recommendations = []
        for model_id in final_indices:
            if model_id == 0:
                continue
            try:
                original_id = self.track_encoder.inverse_transform([model_id - 1])[0]
                row = self.music_df[self.music_df['track_id'] == original_id]
                if not row.empty:
                    track = row.iloc[0]
                    recommendations.append({
                        'title': track['title'],
                        'artist': track['artist'],
                        'genre': track['genre'],
                        'artwork_url': track['artwork_url'],
                        'stream_url': track['stream_url'],
                        'permalink': track['permalink']
                    })
            except:
                pass
        
        return recommendations
    
    def predict_with_audius_api(self, track_names):
        """Fallback: Use Audius API to get similar trending tracks"""
        # Get genre from first matched track
        first_match = self.find_best_match(track_names[0]) if track_names else None
        
        if first_match:
            genre = first_match['genre']
            print(f"🎯 Using genre: {genre}")
        else:
            genre = "Electronic"
        
        # Fetch trending tracks in that genre
        url = "https://api.audius.co/v1/tracks/search"
        params = {
            "app_name": "MusicRecommender",
            "query": genre,
            "limit": 15
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            recommendations = []
            if "data" in data:
                for track in data["data"][:10]:
                    recommendations.append({
                        'title': track.get('title'),
                        'artist': track['user']['name'] if 'user' in track else 'Unknown',
                        'genre': track.get('genre', 'Unknown'),
                        'artwork_url': track['artwork']['1000x1000'] if 'artwork' in track and track['artwork'] else None,
                        'stream_url': f"https://api.audius.co/v1/tracks/{track.get('id')}/stream?app_name=MusicRecommender",
                        'permalink': track.get('permalink')
                    })
            
            return recommendations
        except Exception as e:
            print(f"❌ API fallback error: {e}")
            return []
    
    def predict(self, track_names):
        """
        Main prediction method
        
        Args:
            track_names: List of track names from user
            
        Returns:
            List of recommended tracks with metadata
        """
        if not track_names:
            return []
        
        print(f"🎵 Processing: {track_names}")
        
        # Use model if available, otherwise API fallback
        if self.model_loaded:
            return self.predict_with_model(track_names)
        else:
            return self.predict_with_audius_api(track_names)


# Initialize global recommender instance
try:
    music_engine = MusicRecommender(use_fallback=True)
except Exception as e:
    print(f"⚠️ Could not initialize music recommender: {e}")
    music_engine = None


if __name__ == "__main__":
    print("🎵 Music Recommendation Test\n")
    
    if music_engine:
        # Test with sample tracks
        test_tracks = ["Phony", "TUNER'S GROOVE"]
        recommendations = music_engine.predict(test_tracks)
        
        print(f"\n📋 Recommendations based on: {test_tracks}\n")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec['title']} - {rec['artist']} ({rec['genre']})")
    else:
        print("❌ Music engine not initialized")
