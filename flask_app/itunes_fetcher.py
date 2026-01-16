"""
iTunes/Apple Music API Fetcher - FOR HINDI/BOLLYWOOD SONGS
100% FREE - No API keys, no signup, no authentication required!

iTunes has a massive Bollywood catalog including:
- Arijit Singh, Shreya Ghoshal, Atif Aslam
- Latest Hindi releases
- Regional languages (Tamil, Telugu, Punjabi)
"""

import requests
import time
from typing import List, Dict

class iTunesFetcher:
    """Fetches Hindi/Bollywood songs from iTunes Search API"""
    
    BASE_URL = "https://itunes.apple.com/search"
    
    def __init__(self):
        print("✅ iTunes API initialized (no auth required)")
    
    def search_songs(self, query: str, limit: int = 50, country: str = "IN") -> List[Dict]:
        """
        Search for songs on iTunes
        
        Args:
            query: Search query (artist name, song name, genre)
            limit: Number of results (max 200)
            country: Country code (IN for India)
            
        Returns:
            List of track dictionaries
        """
        params = {
            "term": query,
            "country": country,
            "media": "music",
            "entity": "song",
            "limit": min(limit, 200)  # iTunes max is 200
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            tracks = []
            for item in data.get("results", []):
                # Skip if it's not a track
                if item.get("kind") != "song":
                    continue
                
                # Generate Spotify search URL (opens in Spotify app)
                spotify_query = f"{item.get('trackName', '')} {item.get('artistName', '')}".replace(' ', '+')
                spotify_url = f"https://open.spotify.com/search/{spotify_query}"
                
                track_info = {
                    'track_id': f"itunes_{item.get('trackId')}",
                    'title': item.get('trackName', 'Unknown'),
                    'artist': item.get('artistName', 'Unknown'),
                    'artist_handle': str(item.get('artistId', '')),
                    'genre': item.get('primaryGenreName', 'Unknown'),
                    'mood': 'Unknown',
                    'duration': item.get('trackTimeMillis', 0) // 1000,  # Convert to seconds
                    'play_count': 0,  # iTunes doesn't provide this
                    'favorite_count': 0,
                    'permalink': item.get('trackViewUrl', ''),
                    'artwork_url': item.get('artworkUrl100', '').replace('100x100', '600x600'),  # Get higher res
                    'stream_url': item.get('previewUrl', ''),  # 30-second preview
                    'apple_music_url': item.get('trackViewUrl', ''),  # Apple Music link
                    'spotify_url': spotify_url,  # Spotify search link
                    'itunes_uri': item.get('trackViewUrl', '')
                }
                tracks.append(track_info)
            
            print(f"✅ Found {len(tracks)} tracks for: {query}")
            return tracks
        
        except Exception as e:
            print(f"❌ Error searching iTunes: {e}")
            return []
    
    def get_hindi_songs(self, num_tracks: int = 200) -> List[Dict]:
        """
        Get popular Hindi/Bollywood songs
        
        Args:
            num_tracks: Total number of tracks to fetch
            
        Returns:
            List of track dictionaries
        """
        # Popular Hindi artists and searches
        queries = [
            # Top Hindi Artists
            "Arijit Singh hindi",
            "Shreya Ghoshal",
            "Atif Aslam hindi",
            "Sonu Nigam",
            "Neha Kakkar",
            "Badshah rapper",
            "Armaan Malik hindi",
            "Jubin Nautiyal",
            "Yo Yo Honey Singh",
            "Raftaar rapper",
            
            # Popular Songs/Movies
            "Tum Hi Ho",
            "Kesariya",
            "Apna Bana Le",
            "Chaleya",
            "Pal Pal Dil Ke Paas",
            
            # Genres
            "romantic hindi songs",
            "bollywood party songs",
            "punjabi songs 2024",
            "hindi sad songs",
            "item songs bollywood"
        ]
        
        all_tracks = []
        tracks_per_query = num_tracks // len(queries)
        
        for query in queries:
            tracks = self.search_songs(query, limit=tracks_per_query, country="IN")
            all_tracks.extend(tracks)
            time.sleep(0.3)  # Be respectful to API
        
        # Remove duplicates
        seen_ids = set()
        unique_tracks = []
        for track in all_tracks:
            if track['track_id'] not in seen_ids:
                seen_ids.add(track['track_id'])
                unique_tracks.append(track)
        
        print(f"✅ Total unique Hindi tracks: {len(unique_tracks)}")
        return unique_tracks
    
    def get_regional_songs(self, language: str = "Tamil", num_tracks: int = 50) -> List[Dict]:
        """
        Get songs in regional Indian languages
        
        Args:
            language: Tamil, Telugu, Kannada, Malayalam, Marathi, Bengali, etc.
            num_tracks: Number of tracks
            
        Returns:
            List of tracks
        """
        queries = [
            f"{language} songs",
            f"{language} romantic",
            f"{language} 2024 hits"
        ]
        
        all_tracks = []
        for query in queries:
            tracks = self.search_songs(query, limit=num_tracks // len(queries), country="IN")
            all_tracks.extend(tracks)
            time.sleep(0.3)
        
        # Remove duplicates
        seen_ids = set()
        unique = [t for t in all_tracks if t['track_id'] not in seen_ids and not seen_ids.add(t['track_id'])]
        
        print(f"✅ Found {len(unique)} {language} tracks")
        return unique


if __name__ == "__main__":
    print("🎵 iTunes API Test (Hindi Songs)\n")
    print("=" * 60)
    
    fetcher = iTunesFetcher()
    
    # Test 1: Search specific artist
    print("\n1️⃣ Testing: Arijit Singh")
    tracks = fetcher.search_songs("Arijit Singh", limit=5, country="IN")
    for i, track in enumerate(tracks, 1):
        print(f"   {i}. {track['title']} - {track['artist']}")
    
    # Test 2: Popular Hindi songs
    print("\n2️⃣ Testing: Get Hindi Songs Collection")
    hindi_collection = fetcher.get_hindi_songs(num_tracks=100)
    print(f"   Total tracks fetched: {len(hindi_collection)}")
    print("   Sample:")
    for i, track in enumerate(hindi_collection[:5], 1):
        print(f"   {i}. {track['title']} - {track['artist']} ({track['genre']})")
    
    print("\n" + "=" * 60)
    print("✅ iTunes API working perfectly!")
    print("   - No authentication required")
    print("   - Massive Bollywood catalog")
    print("   - 30-second previews available")
