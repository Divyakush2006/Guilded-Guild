import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import LabelEncoder
from tqdm import tqdm # Progress bar

# CONFIGURATION
MAX_SEQUENCE_LENGTH = 200 # Look at the last 200 movies a user watched
MIN_INTERACTIONS = 5      # Ignore users with < 5 ratings (Noise)

def process_data(filepath):
    print("Loading 25M Dataset... (This will use RAM)")
    # Load only necessary columns to save memory
    df = pd.read_csv(filepath, usecols=['userId', 'movieId', 'rating', 'timestamp'])
    
    # 1. CLEANING: Filter Data
    # Only keep "Liked" movies (Implicit Feedback Strategy)
    # If we want to predict what they will watch next, we focus on what they engaged with (Rating > 3.5)
    df = df[df['rating'] >= 3.5]
    
    # 2. ENCODING: Remap IDs to 1, 2, 3...
    print("Encoding IDs...")
    user_encoder = LabelEncoder()
    item_encoder = LabelEncoder()
    
    df['user_idx'] = user_encoder.fit_transform(df['userId'])
    df['movie_idx'] = item_encoder.fit_transform(df['movieId']) + 1 # +1 because 0 is reserved for padding
    
    num_items = len(item_encoder.classes_) + 1
    print(f"Total Movies: {num_items}, Total interactions: {len(df)}")
    
    # 3. SEQUENCING: Group by User and Sort by Time
    print("Grouping sequences... (This takes time)")
    # Sort by time first
    df = df.sort_values('timestamp')
    
    # Group by user and collect movies into lists
    # Result: User 1: [50, 29, 101, ...]
    user_group = df.groupby('user_idx')['movie_idx'].apply(list)
    
    sequences = []
    
    for user_id, movie_list in tqdm(user_group.items()):
        if len(movie_list) < MIN_INTERACTIONS:
            continue
            
        # Truncate to last N movies (Recency is key for high accuracy)
        seq = movie_list[-MAX_SEQUENCE_LENGTH:]
        sequences.append(seq)
        
    print(f"Generated {len(sequences)} valid user sequences.")
    
    # 4. SAVE EVERYTHING
    print("Saving processed data...")
    with open('processed_sequences.pkl', 'wb') as f:
        pickle.dump(sequences, f)
        
    with open('item_encoder.pkl', 'wb') as f:
        pickle.dump(item_encoder, f)
        
    print("SUCCESS: Data is ready for Transformer Training.")

if __name__ == "__main__":
    # Point this to your 25M file
    process_data('../ml-25m/ratings.csv')