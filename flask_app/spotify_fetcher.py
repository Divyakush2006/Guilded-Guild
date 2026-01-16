"""
Spotify Music Data Fetcher - FOR HINDI/BOLLYWOOD SONGS
This fetcher uses Spotify API to get Hindi songs that Audius doesn't have.

Setup Instructions:
1. Go to https://developer.spotify.com/dashboard
2. Create an app
3. Get your Client ID and Client Secret
4. Create a .env file with:
   SPOTIFY_CLIENT_ID=your_client_id_here
   SPOTIFY_CLIENT_SECRET=your_client_secret_here
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import os
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SpotifyHindiFetcher:
    """Fetches Hindi/Bollywood songs from Spotify"""
    
    def __init__(self):
        """Initialize Spotify client"""
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            raise ValueError(
                "❌ Spotify credentials not found!\n"
                "Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env file"
            )
        
        # Authenticate
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        print("✅ Spotify client initialized")
    
    def search_hindi_songs(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search for Hindi/Bollywood songs
        
        Args:
            query: Search query (e.g., "Arijit Singh", "romantic hindi songs")
            limit: Number of results
            
        Returns:
            List of track dictionaries
        """
        try:
            results = self.sp.search(q=query, type='track', limit=limit, market='IN')
            tracks = []
            
            for item in results['tracks']['items']:
                # Only get complete tracks, not playlists
                if item['type'] == 'track':
                    track_info = {
                        'track_id': f"spotify_{item['id']}",
                        'title': item['name'],
                        'artist': item['artists'][0]['name'],
                        'artist_handle': item['artists'][0]['id'],
                        'genre': 'Bollywood',  # Spotify doesn't always provide genre
                        'mood': 'Unknown',
                        'duration': item['duration_ms'] // 1000,  # Convert to seconds
                        'play_count': item['popularity'] * 1000,  # Use popularity as proxy
                        'favorite_count': 0,
                        'permalink': item['external_urls']['spotify'],
                        'artwork_url': item['album']['images'][0]['url'] if item['album']['images'] else None,
                        'stream_url': item['preview_url'] or item['external_urls']['spotify'],
                        'spotify_uri': item['uri']
                    }
                    tracks.append(track_info)
            
            print(f"✅ Found {len(tracks)} tracks for: {query}")
            return tracks
        
        except Exception as e:
            print(f"❌ Error searching Spotify: {e}")
            return []
    
    def get_popular_hindi_songs(self, num_tracks: int = 200) -> List[Dict]:
        """
        Get popular Hindi/Bollywood songs using predefined queries
        
        Args:
            num_tracks: Total number of tracks to fetch
            
        Returns:
            List of track dictionaries
        """
        # Popular Hindi artists and searches
        queries = [
            "Arijit Singh",
            "Shreya Ghoshal",
            "Atif Aslam",
            "Sonu Nigam",
            "Neha Kakkar",
            "Badshah",
            "Armaan Malik",
            "romantic hindi songs",
            "bollywood party songs",
            "hindi sad songs",
            "punjabi hits",
            "hindi 2024 hits"
        ]
        
        all_tracks = []
        tracks_per_query = num_tracks // len(queries)
        
        for query in queries:
            tracks = self.search_hindi_songs(query, limit=tracks_per_query)
            all_tracks.extend(tracks)
        
        # Remove duplicates
        seen_ids = set()
        unique_tracks = []
        for track in all_tracks:
            if track['track_id'] not in seen_ids:
                seen_ids.add(track['track_id'])
                unique_tracks.append(track)
        
        print(f"✅ Total unique Hindi tracks: {len(unique_tracks)}")
        return unique_tracks
    
    def merge_with_audius_dataset(self, audius_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge Spotify Hindi songs with Audius dataset
        
        Args:
            audius_df: DataFrame from Audius
            
        Returns:
            Combined DataFrame
        """
        # Get Hindi songs
        hindi_tracks = self.get_popular_hindi_songs(200)
        hindi_df = pd.DataFrame(hindi_tracks)
        
        # Combine
        combined_df = pd.concat([audius_df, hindi_df], ignore_index=True)
        print(f"✅ Combined dataset: {len(combined_df)} total tracks")
        print(f"   - Audius: {len(audius_df)} tracks")
        print(f"   - Spotify (Hindi): {len(hindi_df)} tracks")
        
        return combined_df


if __name__ == "__main__":
    print("🎵 Spotify Hindi Music Fetcher Test\n")
    
    try:
        fetcher = SpotifyHindiFetcher()
        
        # Test search
        tracks = fetcher.search_hindi_songs("Arijit Singh romantic", limit=10)
        
        print("\n📋 Sample tracks:")
        for i, track in enumerate(tracks[:5], 1):
            print(f"{i}. {track['title']} - {track['artist']}")
        
        print("\n✅ Spotify integration working!")
        
    except Exception as e:
        print(f"\n❌ Setup required: {e}")
        print("\nTo use Spotify integration:")
        print("1. Go to https://developer.spotify.com/dashboard")
        print("2. Create an app")
        print("3. Copy Client ID and Client Secret")
        print("4. Create .env file with:")
        print("   SPOTIFY_CLIENT_ID=your_id")
        print("   SPOTIFY_CLIENT_SECRET=your_secret")
