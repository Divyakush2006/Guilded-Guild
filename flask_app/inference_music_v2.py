"""
Pre-trained Model Music Recommendation Engine
Uses Sentence Transformers, musicnn, and SASRec for intelligent music recommendations.
Spotify/YouTube used only for playback.
"""

import numpy as np
import pandas as pd
import pickle
from sentence_transformers import SentenceTransformer
import chromadb
from typing import List, Dict, Optional
import os

class MusicRecommenderV2:
    """
    Music recommendation engine using pre-trained models:
    1. Sentence Transformer - Track embeddings
    2. musicnn - Mood/audio feature analysis (to be added)
    3. SASRec - Sequential predictions
    """
    
    def __init__(self, use_vector_db=True):
        print("🎵 Initializing Music Recommender V2 (Pre-trained Models)...")
        
        # Load Sentence Transformer (same as movie system)
        print("📚 Loading Sentence Transformer...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print(f"   ✅ Model loaded: all-MiniLM-L6-v2")
        
        # Initialize Vector DB
        self.use_vector_db = use_vector_db
        if use_vector_db:
            print("💾 Initializing Vector Database...")
            self.chroma_client = chromadb.PersistentClient(path="./music_vectordb")
            self.collection = self.chroma_client.get_or_create_collection(
                name="music_tracks",
                metadata={"description": "Music track embeddings for semantic search"}
            )
            print(f"   ✅ Vector DB ready")
        
        # Load track metadata
        self.load_track_metadata()
        
        print("✅ Music Recommender V2 Ready!\n")
    
    def load_track_metadata(self):
        """Load track metadata from dataset"""
        try:
            if os.path.exists('music_dataset.pkl'):
                self.tracks_df = pd.read_pickle('music_dataset.pkl')
                print(f"📋 Loaded {len(self.tracks_df)} tracks from dataset")
            else:
                print("⚠️ No music dataset found. Run music_data_fetcher.py first.")
                self.tracks_df = pd.DataFrame()
        except Exception as e:
            print(f"⚠️ Error loading dataset: {e}")
            self.tracks_df = pd.DataFrame()
    
    def build_track_embeddings(self, force_rebuild=False):
        """
        Build embeddings for all tracks in dataset
        This is a one-time operation (or when dataset changes)
        """
        if self.tracks_df.empty:
            print("❌ No tracks to embed. Load dataset first.")
            return
        
        # Check if embeddings already exist
        existing_count = self.collection.count()
        if existing_count > 0 and not force_rebuild:
            print(f"ℹ️ Found {existing_count} existing embeddings. Skipping rebuild.")
            print("   Use force_rebuild=True to recreate embeddings.")
            return
        
        print(f"🔧 Building embeddings for {len(self.tracks_df)} tracks...")
        
        documents = []
        metadatas = []
        ids = []
        
        for idx, row in self.tracks_df.iterrows():
            # Create rich description (title + artist + genre)
            description = f"{row['title']} by {row['artist']}. Genre: {row['genre']}"
            
            documents.append(description)
            
            # ChromaDB metadata CANNOT contain None values - convert all to strings
            metadatas.append({
                "track_id": str(row['track_id']),
                "title": str(row['title']),
                "artist": str(row['artist']),
                "genre": str(row['genre']),
                "mood": str(row.get('mood', 'Unknown')),  # Default to 'Unknown' instead of None
                "stream_url": str(row.get('stream_url', '')),
                "artwork_url": str(row.get('artwork_url', ''))
            })
            ids.append(str(row['track_id']))
        
        # Generate embeddings
        print("   Encoding descriptions...")
        embeddings = self.embedding_model.encode(
            documents, 
            show_progress_bar=True,
            batch_size=32
        )
        
        # Store in vector DB
        print("   Storing in vector database...")
        self.collection.add(
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✅ Embeddings complete! {len(ids)} tracks indexed.")
    
    def search_tracks(self, query: str, n_results: int = 10) -> List[Dict]:
        """
        Semantic search for tracks using Sentence Transformer
        
        Args:
            query: User query (e.g., "energetic dubstep", "Phony")
            n_results: Number of results to return
            
        Returns:
            List of track dictionaries with metadata
        """
        if self.collection.count() == 0:
            print("⚠️ No embeddings found. Run build_track_embeddings() first.")
            return []
        
        # Encode query
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        # Search vector DB
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(n_results, self.collection.count())
        )
        
        # Format results
        tracks = []
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            
            # Generate platform URLs
            platform_urls = self.generate_platform_urls(metadata['title'], metadata['artist'])
            
            tracks.append({
                'track_id': metadata['track_id'],
                'title': metadata['title'],
                'artist': metadata['artist'],
                'genre': metadata['genre'],
                'mood': metadata['mood'],
                'stream_url': metadata['stream_url'],
                'artwork_url': metadata['artwork_url'],
                'spotify_url': platform_urls['spotify_url'],
                'apple_music_url': platform_urls['apple_music_url'],
                'permalink': metadata['stream_url'],  # Fallback for template
                'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
            })
        
        return tracks
    
    def generate_platform_urls(self, title: str, artist: str) -> Dict[str, str]:
        """
        Generate search URLs for Spotify and Apple Music
        
        Args:
            title: Track title
            artist: Artist name
            
        Returns:
            Dictionary with spotify_url and apple_music_url
        """
        from urllib.parse import quote_plus
        
        # Create search query
        search_query = f"{title} {artist}"
        encoded_query = quote_plus(search_query)
        
        return {
            'spotify_url': f"https://open.spotify.com/search/{encoded_query}",
            'apple_music_url': f"https://music.apple.com/search?term={encoded_query}"
        }
    
    def find_similar_tracks(self, track_title: str, n_results: int = 10) -> List[Dict]:
        """
        Find tracks similar to a given track
        
        Args:
            track_title: Title of the reference track
            n_results: Number of similar tracks to return
            
        Returns:
            List of similar tracks
        """
        # First find the track itself
        matches = self.search_tracks(track_title, n_results=1)
        
        if not matches:
            return []
        
        reference_track = matches[0]
        
        # Search for similar tracks using the reference track's description
        query = f"{reference_track['title']} {reference_track['artist']} {reference_track['genre']}"
        similar_tracks = self.search_tracks(query, n_results=n_results + 1)
        
        # Remove the reference track itself from results
        similar_tracks = [t for t in similar_tracks if t['track_id'] != reference_track['track_id']]
        
        return similar_tracks[:n_results]
    
    def detect_genre_from_query(self, query: str) -> Optional[str]:
        """
        Detect genre from query string using keywords
        
        Args:
            query: User query string
            
        Returns:
            Detected genre or None
        """
        query_lower = query.lower()
        
        # Genre keyword mapping
        genre_keywords = {
            'Bollywood': ['bollywood', 'hindi', 'indian', 'desi', 'mumbai', 'filmi', 'fevicol', 'kesariya'],
            'Hip-Hop/Rap': ['hip-hop', 'rap', 'hiphop', 'rapper'],
            'Electronic': ['electronic', 'edm', 'electro'],
            'Dubstep': ['dubstep', 'bass', 'wobble'],
            'House': ['house', 'deep house', 'tech house'],
            'Jazz': ['jazz', 'swing', 'bebop'],
            'Pop': ['pop', 'popular'],
            'Rock': ['rock', 'metal', 'punk'],
        }
        
        for genre, keywords in genre_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return genre
        
        return None
    
    def search_by_genre_filter(self, genre: str, n_results: int = 10) -> List[Dict]:
        """
        Search tracks filtered by specific genre
        
        Args:
            genre: Genre to filter by
            n_results: Number of results
            
        Returns:
            List of tracks matching the genre
        """
        if self.tracks_df.empty:
            return []
        
        # Filter dataframe by genre
        genre_tracks = self.tracks_df[self.tracks_df['genre'] == genre]
        
        if len(genre_tracks) == 0:
            print(f"⚠️ No tracks found for genre: {genre}")
            return []
        
        # Sample random tracks from this genre
        sample_size = min(n_results, len(genre_tracks))
        sampled = genre_tracks.sample(n=sample_size)
        
        results = []
        for _, row in sampled.iterrows():
            platform_urls = self.generate_platform_urls(row['title'], row['artist'])
            results.append({
                'track_id': str(row['track_id']),
                'title': row['title'],
                'artist': row['artist'],
                'genre': row['genre'],
                'mood': row.get('mood', 'Unknown'),
                'stream_url': row.get('stream_url', ''),
                'artwork_url': row.get('artwork_url', ''),
                'spotify_url': platform_urls['spotify_url'],
                'apple_music_url': platform_urls['apple_music_url'],
                'permalink': row.get('stream_url', ''),
                'similarity_score': 1.0  # Max score for genre match
            })
        
        return results
    
    def recommend_by_mood(self, mood: str, genre: Optional[str] = None, n_results: int = 10) -> List[Dict]:
        """
        Recommend tracks by mood (and optionally genre)
        
        Args:
            mood: Desired mood (e.g., "energetic", "calm", "romantic")
            genre: Optional genre filter
            n_results: Number of results
            
        Returns:
            List of tracks matching mood/genre
        """
        query = f"{mood} music"
        if genre:
            query += f" {genre}"
        
        return self.search_tracks(query, n_results=n_results)
    
    def predict(self, track_names: List[str]) -> List[Dict]:
        """
        Main prediction method - uses semantic search with genre-aware fallback
        
        Args:
            track_names: List of track names from user
            
        Returns:
            List of recommended tracks
        """
        if not track_names:
            return []
        
        print(f"🎵 Processing: {track_names}")
        
        # Use the first track as query
        query = track_names[0]
        
        # Detect genre from query
        detected_genre = self.detect_genre_from_query(query)
        if detected_genre:
            print(f"   🎯 Detected genre: {detected_genre}")
        
        # Step 1: Try semantic search for similar tracks
        recommendations = self.find_similar_tracks(query, n_results=10)
        
        # Step 2: Check if results are good (high similarity)
        if recommendations and len(recommendations) > 0:
            avg_similarity = sum(r.get('similarity_score', 0) for r in recommendations) / len(recommendations)
            
            # If similarity is good, return results
            if avg_similarity > 0.3:
                print(f"   ✅ Found similar tracks (avg similarity: {avg_similarity:.2f})")
                return recommendations
            else:
                print(f"   ⚠️ Low similarity ({avg_similarity:.2f}), trying genre fallback...")
        
        # Step 3: Genre-aware fallback
        if detected_genre:
            print(f"   🔄 Falling back to genre: {detected_genre}")
            genre_results = self.search_by_genre_filter(detected_genre, n_results=10)
            if genre_results:
                return genre_results
        
        # Step 4: Final fallback - general semantic search
        if not recommendations:
            print(f"   🔄 Using general semantic search...")
            recommendations = self.search_tracks(query, n_results=10)
        
        return recommendations


# Global instance
music_engine_v2 = None

def initialize_engine():
    """Initialize the music engine (call once)"""
    global music_engine_v2
    try:
        music_engine_v2 = MusicRecommenderV2(use_vector_db=True)
        
        # Build embeddings if needed
        if music_engine_v2.collection.count() == 0:
            print("\n🔧 First-time setup: Building track embeddings...")
            music_engine_v2.build_track_embeddings()
        
        return music_engine_v2
    except Exception as e:
        print(f"❌ Failed to initialize music engine: {e}")
        return None


if __name__ == "__main__":
    print("🎵 Music Recommender V2 - Pre-trained Models Test\n")
    print("=" * 60)
    
    # Initialize
    engine = initialize_engine()
    
    if engine and engine.collection.count() > 0:
        print("\n" + "=" * 60)
        print("🧪 Testing Recommendations\n")
        
        # Test 1: Semantic search
        print("1️⃣ Semantic Search Test:")
        query = "energetic dubstep bass"
        results = engine.search_tracks(query, n_results=5)
        print(f"   Query: '{query}'")
        for i, track in enumerate(results, 1):
            print(f"   {i}. {track['title']} - {track['artist']} ({track['genre']}) [{track['similarity_score']:.2f}]")
        
        # Test 2: Find similar
        print("\n2️⃣ Similar Tracks Test:")
        if results:
            ref_track = results[0]['title']
            similar = engine.find_similar_tracks(ref_track, n_results=5)
            print(f"   Similar to: '{ref_track}'")
            for i, track in enumerate(similar, 1):
                print(f"   {i}. {track['title']} - {track['artist']}")
        
        # Test 3: Mood-based
        print("\n3️⃣ Mood-based Recommendations:")
        mood_tracks = engine.recommend_by_mood("calm", genre="Jazz", n_results=5)
        print(f"   Mood: calm, Genre: Jazz")
        for i, track in enumerate(mood_tracks, 1):
            print(f"   {i}. {track['title']} - {track['artist']}")
        
        print("\n" + "=" * 60)
        print("✅ All tests complete!")
    else:
        print("\n❌ Could not initialize engine. Check dataset and dependencies.")
