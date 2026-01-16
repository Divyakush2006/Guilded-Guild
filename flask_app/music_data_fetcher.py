"""
Audius Music Data Fetcher
Fetches trending and searched music tracks from Audius API to build dataset for recommendations.
"""

import requests
import pickle
import pandas as pd
from typing import List, Dict, Optional
import time

class AudiusMusicFetcher:
    """Fetches music data from Audius API"""
    
    BASE_URL = "https://api.audius.co/v1"
    APP_NAME = "MusicRecommender"  # Required parameter for Audius API
    
    def __init__(self):
        self.tracks_data = []
        
    def fetch_trending_tracks(self, limit: int = 100) -> List[Dict]:
        """
        Fetch trending tracks from Audius
        
        Args:
            limit: Number of tracks to fetch
            
        Returns:
            List of track dictionaries
        """
        url = f"{self.BASE_URL}/tracks/trending"
        params = {
            "app_name": self.APP_NAME,
            "limit": limit
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "data" in data:
                print(f"✅ Fetched {len(data['data'])} trending tracks")
                return data["data"]
            return []
        except Exception as e:
            print(f"❌ Error fetching trending tracks: {e}")
            return []
    
    def search_tracks_by_genre(self, genre: str, limit: int = 50) -> List[Dict]:
        """
        Search tracks by genre/mood
        
        Args:
            genre: Genre name (e.g., "Dubstep", "House", "Electronic")
            limit: Number of results
            
        Returns:
            List of track dictionaries
        """
        url = f"{self.BASE_URL}/tracks/search"
        params = {
            "app_name": self.APP_NAME,
            "query": genre,
            "limit": limit
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "data" in data:
                print(f"✅ Found {len(data['data'])} tracks for genre: {genre}")
                return data["data"]
            return []
        except Exception as e:
            print(f"❌ Error searching {genre}: {e}")
            return []
    
    
    def is_playlist_or_mix(self, title: str) -> bool:
        """
        Check if track title indicates it's a playlist/mix/compilation
        
        Args:
            title: Track title
            
        Returns:
            True if it's a playlist/mix, False if it's a single song
        """
        title_lower = title.lower()
        
        # Keywords that indicate playlists/mixes
        playlist_keywords = [
            'mix', 'playlist', 'compilation', 'set', 'session',
            'mixtape', 'ep ', 'album', 'collection', 'best of',
            'vol.', 'volume', 'part ', 'pt.', '|', 'continuous',
            'hour', 'hours', 'non-stop', 'nonstop', 'medley'
        ]
        
        # Check for keywords
        for keyword in playlist_keywords:
            if keyword in title_lower:
                return True
        
        # Check for duration indicators (mixes are usually long)
        # Pattern: "30 min", "1 hour", etc.
        import re
        if re.search(r'\d+\s*(min|hour|hr)', title_lower):
            return True
        
        return False
    
    def extract_track_info(self, track: Dict) -> Dict:
        """
        Extract relevant information from track data
        
        Args:
            track: Raw track data from Audius API
            
        Returns:
            Cleaned track info dictionary
        """
        title = track.get("title", "Unknown")
        artist = track["user"]["name"] if "user" in track else "Unknown"
        
        # Generate search URLs for Spotify and Apple Music
        search_query = f"{title} {artist}".replace(' ', '+')
        spotify_url = f"https://open.spotify.com/search/{search_query}"
        apple_music_url = f"https://music.apple.com/search?term={search_query}"
        
        return {
            "track_id": track.get("id"),
            "title": title,
            "artist": artist,
            "artist_handle": track["user"]["handle"] if "user" in track else "",
            "genre": track.get("genre", "Unknown"),
            "mood": track.get("mood") or "Unknown",
            "duration": track.get("duration", 0),
            "play_count": track.get("play_count", 0),
            "favorite_count": track.get("favorite_count", 0),
            "permalink": track.get("permalink"),
            "artwork_url": track["artwork"]["1000x1000"] if "artwork" in track and track["artwork"] else None,
            "stream_url": f"https://api.audius.co/v1/tracks/{track.get('id')}/stream?app_name={self.APP_NAME}",
            "spotify_url": spotify_url,
            "apple_music_url": apple_music_url
        }
    
    def build_dataset(self, num_trending: int = 500, genres: List[str] = None) -> pd.DataFrame:
        """
        Build a comprehensive music dataset
        
        Args:
            num_trending: Number of trending tracks to fetch
            genres: List of genres to search (if None, use default popular genres)
            
        Returns:
            DataFrame with track information
        """
        if genres is None:
            # Popular genres on Audius
            genres = [
                "Dubstep", "House", "Electronic", "Trap", "Hip-Hop/Rap",
                "Techno", "Deep House", "Drum & Bass", "Pop", "Jazz",
                "Experimental", "Tech House", "Future Bass"
            ]
        
        all_tracks = []
        
        # Fetch trending tracks
        print(f"📊 Fetching {num_trending} trending tracks...")
        trending = self.fetch_trending_tracks(limit=num_trending)
        all_tracks.extend(trending)
        
        # Fetch tracks by genre
        print(f"📊 Fetching tracks from {len(genres)} genres...")
        for genre in genres:
            tracks = self.search_tracks_by_genre(genre, limit=50)
            all_tracks.extend(tracks)
            time.sleep(0.5)  # Be respectful even though no rate limit
        
    def build_dataset(self, num_trending: int = 500, genres: List[str] = None, filter_playlists: bool = True) -> pd.DataFrame:
        """
        Build a comprehensive music dataset
        
        Args:
            num_trending: Number of trending tracks to fetch
            genres: List of genres to search (if None, use default popular genres)
            filter_playlists: If True, exclude playlists/mixes (default: True)
            
        Returns:
            DataFrame with track information
        """
        if genres is None:
            # Popular genres on Audius + Hindi/Bollywood
            genres = [
                "Dubstep", "House", "Electronic", "Trap", "Hip-Hop/Rap",
                "Techno", "Deep House", "Drum & Bass", "Pop", "Jazz",
                "Experimental", "Tech House", "Future Bass",
                "Bollywood", "Hindi", "Indian", "Indie"  # Added Hindi genres
            ]
        
        all_tracks = []
        
        # Fetch trending tracks
        print(f"📊 Fetching {num_trending} trending tracks...")
        trending = self.fetch_trending_tracks(limit=num_trending)
        all_tracks.extend(trending)
        
        # Fetch tracks by genre
        print(f"📊 Fetching tracks from {len(genres)} genres...")
        for genre in genres:
            tracks = self.search_tracks_by_genre(genre, limit=50)
            all_tracks.extend(tracks)
            time.sleep(0.5)  # Be respectful even though no rate limit
        
        # Extract and clean data
        print(f"🔧 Processing {len(all_tracks)} tracks...")
        cleaned_tracks = []
        seen_ids = set()
        filtered_count = 0
        
        for track in all_tracks:
            track_id = track.get("id")
            title = track.get("title", "")
            
            if track_id and track_id not in seen_ids:
                # Filter playlists/mixes if enabled
                if filter_playlists and self.is_playlist_or_mix(title):
                    filtered_count += 1
                    continue
                
                seen_ids.add(track_id)
                cleaned_tracks.append(self.extract_track_info(track))
        
        df = pd.DataFrame(cleaned_tracks)
        print(f"✅ Dataset ready: {len(df)} unique tracks")
        if filter_playlists:
            print(f"   🚫 Filtered out {filtered_count} playlists/mixes")
        return df
    
    def save_dataset(self, df: pd.DataFrame, filepath: str = "music_dataset.pkl"):
        """Save dataset to pickle file"""
        df.to_pickle(filepath)
        print(f"💾 Saved dataset to {filepath}")
    
    def create_encoders(self, df: pd.DataFrame):
        """
        Create label encoders for tracks and artists (similar to movie system)
        
        Args:
            df: Music dataset DataFrame
            
        Returns:
            Tuple of (track_encoder, artist_encoder)
        """
        from sklearn.preprocessing import LabelEncoder
        
        track_encoder = LabelEncoder()
        artist_encoder = LabelEncoder()
        
        track_encoder.fit(df['track_id'].values)
        artist_encoder.fit(df['artist_handle'].values)
        
        # Save encoders
        with open('track_encoder.pkl', 'wb') as f:
            pickle.dump(track_encoder, f)
        
        with open('artist_encoder.pkl', 'wb') as f:
            pickle.dump(artist_encoder, f)
        
        print(f"✅ Created encoders:")
        print(f"   - Tracks: {len(track_encoder.classes_)} unique tracks")
        print(f"   - Artists: {len(artist_encoder.classes_)} unique artists")
        
        return track_encoder, artist_encoder


if __name__ == "__main__":
    # Test the data fetcher
    print("🎵 Audius Music Data Fetcher Test\n")
    
    fetcher = AudiusMusicFetcher()
    
    # Build dataset
    df = fetcher.build_dataset(num_trending=200)
    
    # Show sample
    print("\n📋 Sample tracks:")
    print(df[['title', 'artist', 'genre', 'play_count']].head(10))
    
    # Save dataset
    fetcher.save_dataset(df, "music_dataset.pkl")
    
    # Create encoders
    fetcher.create_encoders(df)
    
    print("\n✅ Data fetching complete!")
