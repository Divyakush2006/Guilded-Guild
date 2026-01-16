import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pickle

# CONFIGURATION
# If you have a GPU (Nvidia), this runs 50x faster. If not, it uses CPU.
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE = 2048  # Process 2048 ratings at a time
EPOCHS = 5

print(f"Running on: {DEVICE}")

# 1. CUSTOM DATASET CLASS (The "Feeder")
class MovieLensDataset(Dataset):
    def __init__(self, users, movies, ratings):
        self.users = torch.tensor(users, dtype=torch.long)
        self.movies = torch.tensor(movies, dtype=torch.long)
        self.ratings = torch.tensor(ratings, dtype=torch.float32)

    def __len__(self):
        return len(self.users)

    def __getitem__(self, idx):
        return self.users[idx], self.movies[idx], self.ratings[idx]

# 2. DATA PREPROCESSING
def load_data(filepath):
    print("Loading Dataset... (This takes a moment)")
    
    # MEMORY SAFETY TIP: 
    # If your PC crashes, add nrows=1000000 inside read_csv to test with just 1 million rows first.
    # df = pd.read_csv(filepath, usecols=['userId', 'movieId', 'rating'], nrows=1000000)
    
    df = pd.read_csv(filepath, usecols=['userId', 'movieId', 'rating'])
    
    # ENCODING: The IDs are like 1, 500, 10000. 
    # Deep Learning needs them to be 0, 1, 2, 3... in order.
    user_encoder = LabelEncoder()
    movie_encoder = LabelEncoder()
    
    df['user_idx'] = user_encoder.fit_transform(df['userId'])
    df['movie_idx'] = movie_encoder.fit_transform(df['movieId'])
    
    return df, user_encoder, movie_encoder

class NCF(nn.Module):
    def __init__(self, num_users, num_items, embedding_dim=32):
        super(NCF, self).__init__()
        
        # User & Item Embeddings for the GMF part (Generalized Matrix Factorization)
        self.user_embedding_gmf = nn.Embedding(num_users, embedding_dim)
        self.item_embedding_gmf = nn.Embedding(num_items, embedding_dim)
        
        # User & Item Embeddings for the MLP part (Multi-Layer Perceptron)
        self.user_embedding_mlp = nn.Embedding(num_users, embedding_dim)
        self.item_embedding_mlp = nn.Embedding(num_items, embedding_dim)
        
        # The Neural Network Layers (The "Deep" part)
        # Concatenating User + Item vectors means input is size (dim * 2)
        self.mlp_layers = nn.Sequential(
            nn.Linear(embedding_dim * 2, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU()
        )
        
        # Final Prediction Layer (Combines GMF and MLP)
        self.final_layer = nn.Linear(embedding_dim + 16, 1)
        self.sigmoid = nn.Sigmoid() # Force output between 0 and 1

    def forward(self, user_indices, item_indices):
        # 1. GMF Branch (Dot Product)
        user_gmf = self.user_embedding_gmf(user_indices)
        item_gmf = self.item_embedding_gmf(item_indices)
        gmf_output = user_gmf * item_gmf # Element-wise product
        
        # 2. MLP Branch (Neural Net)
        user_mlp = self.user_embedding_mlp(user_indices)
        item_mlp = self.item_embedding_mlp(item_indices)
        mlp_input = torch.cat([user_mlp, item_mlp], dim=1) # Stack them
        mlp_output = self.mlp_layers(mlp_input)
        
        # 3. Concatenate and Predict
        final_input = torch.cat([gmf_output, mlp_output], dim=1)
        output = self.final_layer(final_input)
        
        return self.sigmoid(output).squeeze()

# --- MAIN EXECUTION (Fixed Indentation) ---
if __name__ == "__main__":
    
    # --- LOAD DATA ---
    # MAKE SURE THIS PATH IS CORRECT FOR YOUR FOLDER
    df, user_enc, movie_enc = load_data('../ml-25m/ratings.csv') 
    
    num_users = len(user_enc.classes_)
    num_items = len(movie_enc.classes_)
    
    print(f"Users: {num_users}, Movies: {num_items}")

    # --- SPLIT DATA ---
    # We treat rating >= 3.5 as "Like" (1) and < 3.5 as "Dislike" (0)
    df['target'] = df['rating'].apply(lambda x: 1 if x >= 3.5 else 0)
    
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
    
    train_dataset = MovieLensDataset(train_df['user_idx'].values, train_df['movie_idx'].values, train_df['target'].values)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    # --- INITIALIZE MODEL ---
    model = NCF(num_users, num_items).to(DEVICE)
    loss_function = nn.BCELoss() # Binary Cross Entropy (Good for Yes/No prediction)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # --- TRAINING LOOP ---
    print("Starting Training...")
    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0
        
        for batch_i, (users, items, ratings) in enumerate(train_loader):
            users, items, ratings = users.to(DEVICE), items.to(DEVICE), ratings.to(DEVICE)
            
            optimizer.zero_grad()
            predictions = model(users, items)
            loss = loss_function(predictions, ratings)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
            if batch_i % 100 == 0:
                print(f"Epoch {epoch+1} | Batch {batch_i}/{len(train_loader)} | Loss: {loss.item():.4f}")
        
        print(f"--- Epoch {epoch+1} Complete. Avg Loss: {total_loss/len(train_loader):.4f} ---")
    
    # --- SAVE THE MODEL ---
    print("Saving Model...")
    torch.save(model.state_dict(), "ncf_model_25m.pth")
    
    # Save encoders too (we need them to decode IDs later)
    with open("user_encoder.pkl", "wb") as f: pickle.dump(user_enc, f)
    with open("movie_encoder.pkl", "wb") as f: pickle.dump(movie_enc, f)
    print("Training Complete. Model Saved.")