import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import pickle
from train_ncf import NCF  # Import the class architecture we defined earlier

# CONFIGURATION
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = "ncf_model_25m.pth"

# 1. LOAD THE ENCODERS (The Translators)
print("Loading dictionaries...")
with open("user_encoder.pkl", "rb") as f:
    user_encoder = pickle.load(f)
with open("movie_encoder.pkl", "rb") as f:
    movie_encoder = pickle.load(f)

# 2. LOAD THE MODEL (The Brain)
print("Loading model...")
num_users = len(user_encoder.classes_)
num_items = len(movie_encoder.classes_)

model = NCF(num_users, num_items).to(DEVICE)
model.load_state_dict(torch.load(MODEL_PATH))
model.eval() # Set to "Evaluation Mode" (turns off training features like Dropout)
print("Model loaded successfully!")

# 3. PREDICTION FUNCTION
def predict_probability(user_id, movie_id):
    """
    Input: Real User ID (e.g., 1) and Real Movie ID (e.g., 50)
    Output: Probability (0.0 to 1.0)
    """
    try:
        # Translate Real ID -> Model ID
        user_idx = user_encoder.transform([user_id])[0]
        movie_idx = movie_encoder.transform([movie_id])[0]
        
        # Convert to Tensor
        user_tensor = torch.tensor([user_idx]).to(DEVICE)
        item_tensor = torch.tensor([movie_idx]).to(DEVICE)
        
        # Predict
        with torch.no_grad():
            prediction = model(user_tensor, item_tensor)
            return prediction.item()
            
    except ValueError:
        # ID not found in training data
        return 0.0

# 4. TEST IT
# Let's test with User 1 (who typically likes Toy Story)
print("\n--- Testing Prediction for User 1 ---")

# Movie ID 1 is "Toy Story (1995)"
prob_toy_story = predict_probability(user_id=1, movie_id=1)
print(f"Probability User 1 likes Toy Story (ID:1): {prob_toy_story:.4f}")

# Movie ID 65 is "Bio-Dome (1996)" (A poorly rated comedy)
prob_bad_movie = predict_probability(user_id=1, movie_id=65)
print(f"Probability User 1 likes Bio-Dome (ID:65): {prob_bad_movie:.4f}")