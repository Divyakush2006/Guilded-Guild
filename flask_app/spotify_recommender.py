"""
Spotify Music Recommendation Engine (V3 - Genre/Style Matching)
Uses Spotify search with genre keywords to find similar style songs.
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define genre/style mappings for better recommendations
GENRE_KEYWORDS = {
    # Bollywood Item Songs / Party Songs
    'item_songs': {
        'tracks': ['sheila ki jawani', 'fevicol se', 'munni badnaam', 'chikni chameli', 
                   'baby doll', 'laila', 'lovely', 'nachde ne saare', 'dilbar', 
                   'kusu kusu', 'haaye garmi', 'kamariya', 'oo antava'],
        'search_terms': ['bollywood item song', 'bollywood party song', 'bollywood dance number',
                        'hindi item number', 'bollywood cabaret', 'hindi party dance'],
        'artists': ['Sunidhi Chauhan', 'Neha Kakkar', 'Badshah', 'Nora Fatehi']
    },
    # Romantic Bollywood
    'romantic_hindi': {
        'tracks': ['tum hi ho', 'kal ho naa ho', 'kabira', 'tere liye', 'pehla nasha',
                   'kesariya', 'raataan lambiyan', 'tera ban jaunga'],
        'search_terms': ['bollywood romantic song', 'hindi love song', 'romantic hindi'],
        'artists': ['Arijit Singh', 'Armaan Malik', 'Atif Aslam']
    },
    # Sad Bollywood
    'sad_hindi': {
        'tracks': ['channa mereya', 'phir bhi tumko chaahunga', 'tujhe bhula diya',
                   'bekhayali', 'tu jaane na'],
        'search_terms': ['hindi sad song', 'bollywood sad song', 'hindi breakup song'],
        'artists': ['Arijit Singh', 'KK', 'Mohit Chauhan']
    },
    # English Pop
    'english_pop': {
        'tracks': ['shape of you', 'blinding lights', 'stay', 'levitating', 'peaches'],
        'search_terms': ['pop hits', 'top pop songs', 'pop music'],
        'artists': ['Ed Sheeran', 'The Weeknd', 'Dua Lipa', 'Justin Bieber']
    },
    # English Party/Dance
    'english_party': {
        'tracks': ['uptown funk', 'dance monkey', "can't stop the feeling", 'happy'],
        'search_terms': ['dance pop', 'party songs', 'upbeat pop'],
        'artists': ['Bruno Mars', 'Doja Cat', 'Lizzo']
    }
}


class SpotifyRecommender:
    """
    Music recommendation engine using Spotify's API.
    Uses genre/style matching for better similar song recommendations.
    """
    
    def __init__(self):
        """Initialize Spotify client"""
        try:
            import spotipy
            from spotipy.oauth2 import SpotifyClientCredentials
            
            client_id = os.getenv("SPOTIFY_CLIENT_ID")
            client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
            
            if not client_id or not client_secret:
                raise ValueError(
                    "Spotify credentials not found. "
                    "Please run: python setup_spotify.py"
                )
            
            # Authenticate
            auth_manager = SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            self.initialized = True
            print("✅ Spotify Recommender initialized (V3 - Genre Matching)")
            
        except ImportError:
            print("❌ spotipy not installed. Run: pip install spotipy python-dotenv")
            self.initialized = False
            self.sp = None
        except Exception as e:
            print(f"❌ Spotify init error: {e}")
            self.initialized = False
            self.sp = None
    
    def detect_genre(self, track_name: str, history: List[str] = None) -> str:
        """
        Detect the genre/style of input tracks.
        Returns the genre key that best matches the input.
        """
        all_tracks = [track_name.lower()]
        if history:
            all_tracks.extend([h.lower().strip() for h in history])
        
        # Check each genre for matches
        genre_scores = {}
        for genre_key, genre_data in GENRE_KEYWORDS.items():
            score = 0
            for track in all_tracks:
                for known_track in genre_data['tracks']:
                    if known_track in track or track in known_track:
                        score += 2
                    # Partial match
                    elif any(word in track for word in known_track.split()):
                        score += 1
            genre_scores[genre_key] = score
        
        # Get best matching genre
        best_genre = max(genre_scores, key=genre_scores.get)
        if genre_scores[best_genre] > 0:
            return best_genre
        
        # Default based on language detection
        hindi_indicators = ['ki', 'ka', 'se', 'ko', 'hai', 'tu', 'tum', 'dil']
        is_hindi = any(word in track_name.lower() for word in hindi_indicators)
        return 'item_songs' if is_hindi else 'english_pop'
    
    def search_by_genre(self, genre_key: str, exclude_tracks: set, limit: int = 15, market: str = "IN") -> List[Dict]:
        """
        Search for tracks matching a specific genre/style.
        """
        if not self.initialized or genre_key not in GENRE_KEYWORDS:
            return []
        
        genre_data = GENRE_KEYWORDS[genre_key]
        results = []
        
        # Search using genre search terms
        for search_term in genre_data['search_terms'][:3]:
            try:
                search_results = self.sp.search(q=search_term, type='track', limit=10, market=market)
                for track in search_results['tracks']['items']:
                    track_key = track['name'].lower()
                    if track_key not in exclude_tracks:
                        exclude_tracks.add(track_key)
                        results.append(self._format_track(track))
            except Exception as e:
                print(f"Search error for '{search_term}': {e}")
        
        # Also search by known artists in this genre
        for artist_name in genre_data.get('artists', [])[:2]:
            try:
                search_results = self.sp.search(q=f"artist:{artist_name}", type='track', limit=5, market=market)
                for track in search_results['tracks']['items']:
                    track_key = track['name'].lower()
                    if track_key not in exclude_tracks:
                        exclude_tracks.add(track_key)
                        results.append(self._format_track(track))
            except Exception as e:
                print(f"Artist search error: {e}")
        
        return results[:limit]
    
    def search_track(self, query: str, market: str = "IN") -> Optional[Dict]:
        """Search for a specific track."""
        if not self.initialized:
            return None
        
        try:
            results = self.sp.search(q=query, type='track', limit=1, market=market)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                return {
                    'id': track['id'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'artist_id': track['artists'][0]['id'],
                    'spotify_url': track['external_urls']['spotify']
                }
            return None
        except Exception as e:
            print(f"Search error: {e}")
            return None
    
    def get_artist_top_tracks(self, artist_id: str, market: str = "IN") -> List[Dict]:
        """Get top tracks from an artist."""
        if not self.initialized:
            return []
        
        try:
            results = self.sp.artist_top_tracks(artist_id, country=market)
            return [self._format_track(track) for track in results['tracks'][:5]]
        except Exception as e:
            print(f"Top tracks error: {e}")
            return []
    
    def _format_track(self, track: dict) -> Dict:
        """Format a Spotify track into our standard format."""
        return {
            'title': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'artwork_url': track['album']['images'][0]['url'] if track['album']['images'] else '',
            'spotify_url': track['external_urls']['spotify'],
            'preview_url': track.get('preview_url', ''),
            'popularity': track['popularity']
        }
    
    def predict(self, current_track: str, history: List[str] = None) -> List[Dict]:
        """
        Main prediction method - finds similar songs using genre matching.
        
        Strategy:
        1. Detect the genre/style of input
        2. Search for songs in that same genre
        3. Add some from related artists
        4. Sort by popularity
        """
        if not self.initialized:
            print("❌ Spotify not initialized")
            return []
        
        print(f"🎵 Finding similar songs for: {current_track}")
        if history:
            print(f"   History: {history}")
        
        # Step 1: Detect genre from input
        genre = self.detect_genre(current_track, history)
        print(f"   🎯 Detected genre/style: {genre}")
        
        recommendations = []
        seen_tracks = set()
        
        # Add input tracks to exclusion list
        seen_tracks.add(current_track.lower())
        if history:
            for h in history:
                seen_tracks.add(h.lower().strip())
        
        # Step 2: Search for the current track to get its artist
        current = self.search_track(current_track)
        if current:
            print(f"   ✅ Found: {current['name']} by {current['artist']}")
            seen_tracks.add(current['name'].lower())
            
            # Get more tracks from the same artist
            artist_tracks = self.get_artist_top_tracks(current['artist_id'])
            for track in artist_tracks:
                track_key = track['title'].lower()
                if track_key not in seen_tracks:
                    seen_tracks.add(track_key)
                    recommendations.append(track)
        
        # Step 3: Get genre-based recommendations
        genre_tracks = self.search_by_genre(genre, seen_tracks, limit=15)
        recommendations.extend(genre_tracks)
        
        # Step 4: If we have history, also search those artists
        if history:
            for song in history[:2]:
                hist_track = self.search_track(song.strip())
                if hist_track:
                    seen_tracks.add(hist_track['name'].lower())
                    hist_artist_tracks = self.get_artist_top_tracks(hist_track['artist_id'])
                    for track in hist_artist_tracks[:3]:
                        track_key = track['title'].lower()
                        if track_key not in seen_tracks:
                            seen_tracks.add(track_key)
                            recommendations.append(track)
        
        # Sort by popularity and return top 10
        recommendations.sort(key=lambda x: x.get('popularity', 0), reverse=True)
        
        print(f"   ✅ Found {len(recommendations)} similar songs")
        return recommendations[:10]


# Global instance
spotify_recommender = None

def initialize_spotify_recommender():
    """Initialize the Spotify recommender (call once)"""
    global spotify_recommender
    try:
        spotify_recommender = SpotifyRecommender()
        return spotify_recommender if spotify_recommender.initialized else None
    except Exception as e:
        print(f"❌ Failed to initialize Spotify recommender: {e}")
        return None


if __name__ == "__main__":
    print("🎵 Spotify Recommender Test (V3 - Genre Matching)\n")
    print("=" * 60)
    
    engine = initialize_spotify_recommender()
    
    if engine and engine.initialized:
        # Test 1: Bollywood Item Songs
        print("\n🧪 Test 1: Bollywood Item Songs")
        recs = engine.predict(
            current_track="Sheila Ki Jawani",
            history=["Fevicol Se", "Munni Badnaam"]
        )
        
        if recs:
            print("\nRecommendations (should be item songs!):")
            for i, track in enumerate(recs[:8], 1):
                print(f"   {i}. {track['title']} - {track['artist']}")
        
        # Test 2: English Pop
        print("\n🧪 Test 2: English Pop Songs")
        recs = engine.predict(
            current_track="Shape of You",
            history=["Blinding Lights"]
        )
        
        if recs:
            print("\nRecommendations:")
            for i, track in enumerate(recs[:5], 1):
                print(f"   {i}. {track['title']} - {track['artist']}")
        
        print("\n" + "=" * 60)
        print("✅ All tests complete!")
    else:
        print("\n❌ Could not initialize.")
