import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD
import difflib 
import re # NEW: Regex for cleaning strings

# GLOBAL VARIABLES
user_movie_matrix_filled = None
corr_matrix = None
movie_names = None
search_map = {} # NEW: Maps "clean names" to "real names"

def normalize_string(text):
    """
    Turns 'Spider-Man: Home (2023)' into 'spidermanhome'
    1. Lowercase
    2. Remove (Year)
    3. Remove all non-alphanumeric characters (spaces, dashes, colons)
    """
    # Remove the year parenthesis part like (1995)
    text = re.sub(r'\(\d{4}\)', '', text)
    # Lowercase and keep only letters/numbers
    return re.sub(r'[^a-z0-9]', '', text.lower())

def load_data():
    """Loads data and trains model. Run this ONCE when server starts."""
    global user_movie_matrix_filled, corr_matrix, movie_names, search_map
    
    if corr_matrix is not None:
        return 

    print("Loading dataset...")
    # Ensure paths are correct
    ratings = pd.read_csv('../ml-latest-small/ratings.csv')
    movies = pd.read_csv('../ml-latest-small/movies.csv')
    
    data = pd.merge(ratings, movies, on='movieId')
    
    # Create Matrix
    user_movie_matrix = data.pivot_table(index='userId', columns='title', values='rating')
    user_movie_matrix_filled = user_movie_matrix.fillna(0)
    
    # Transpose for Item-Item Logic
    X = user_movie_matrix_filled.T
    movie_names = list(X.index)
    
    # --- NEW: BUILD SEARCH INDEX ---
    # Create a map where 'ironman' -> 'Iron Man (2008)'
    print("Building Search Index...")
    for real_name in movie_names:
        clean_name = normalize_string(real_name)
        # Store it. If duplicate, we keep the first one found (usually the older/original movie)
        if clean_name not in search_map:
            search_map[clean_name] = real_name

    # Train SVD
    SVD = TruncatedSVD(n_components=20, random_state=42)
    matrix_features = SVD.fit_transform(X)
    corr_matrix = np.corrcoef(matrix_features)
    print("Model Trained and Ready!")

def find_closest_title(user_input):
    """Robust search that handles 'IRON MAN', 'spider-man', etc."""
    if not user_input: return None
    
    # 1. CLEAN THE USER INPUT (e.g., "IRON MAN" -> "ironman")
    clean_input = normalize_string(user_input)
    
    # 2. EXACT MATCH IN CLEAN MAP
    # If user typed "ironman" and we have "ironman" in our map
    if clean_input in search_map:
        return search_map[clean_input]
    
    # 3. SUBSTRING MATCH (Fallback)
    # If user typed "potter", find "harrypotter..."
    for key in search_map:
        if clean_input in key:
            return search_map[key]
            
    # 4. DIFFLIB (Last Resort)
    # If they typed "Iron Mn" (typo), this catches it
    matches = difflib.get_close_matches(clean_input, list(search_map.keys()), n=1, cutoff=0.4)
    if matches:
        return search_map[matches[0]]
        
    return None

def get_recommendations_from_input(current_movie_input, history_input):
    if corr_matrix is None:
        load_data()
        
    results = {
        "current_context": [],
        "history_based": [],
        "debug_info": []
    }
    
    current_movie_idx = -1

    # 1. PROCESS CURRENT MOVIE
    real_current_title = find_closest_title(current_movie_input)
    
    if real_current_title:
        results['debug_info'].append(f"Input '{current_movie_input}' matched to -> '{real_current_title}'")
        try:
            current_movie_idx = movie_names.index(real_current_title)
            corr_scores = corr_matrix[current_movie_idx]
            top_indices = np.argsort(corr_scores)[-6:-1][::-1]
            for idx in top_indices:
                results['current_context'].append(movie_names[idx])
        except Exception as e:
            results['debug_info'].append(f"Error: {e}")
    else:
        results['debug_info'].append(f"Could not find: '{current_movie_input}'")

    # 2. PROCESS HISTORY
    if history_input:
        history_list = [x.strip() for x in history_input.split(',')]
        valid_history_indices = []
        
        for item in history_list:
            if not item: continue
            real_title = find_closest_title(item)
            if real_title:
                try:
                    idx = movie_names.index(real_title)
                    valid_history_indices.append(idx)
                except: pass
            else:
                results['debug_info'].append(f"Ignored history item: '{item}'")
        
        if valid_history_indices:
            combined_scores = np.zeros(corr_matrix.shape[0])
            for idx in valid_history_indices:
                combined_scores += corr_matrix[idx]
            
            top_history_indices = np.argsort(combined_scores)[::-1]
            
            count = 0
            for idx in top_history_indices:
                if idx not in valid_history_indices and idx != current_movie_idx: 
                    results['history_based'].append(movie_names[idx])
                    count += 1
                    if count >= 5: break
    
    return results