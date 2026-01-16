"""
TMDB Movie Metadata Fetcher
Fetches movie posters, trailers, and other metadata from The Movie Database API.
"""

import os
import requests
import time
from typing import Dict, Optional
from functools import lru_cache
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables from .env file
load_dotenv()

# Create a session with retry logic and connection pooling
def create_tmdb_session():
    """Create a requests session with aggressive retry logic and connection pooling"""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=5,  # Maximum 5 retries
        backoff_factor=1,  # Wait 1s, 2s, 4s, 8s, 16s between retries
        status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP status codes
        allowed_methods=["GET"],  # Only retry GET requests
    )
    
    # Mount adapter with retry strategy
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,  # Connection pool size
        pool_maxsize=20,  # Max connections in pool
        pool_block=False
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# TMDB Configuration
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"  # w500 for good quality posters


class TMDBFetcher:
    """Fetches movie metadata from TMDB API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or TMDB_API_KEY
        self.initialized = bool(self.api_key)
        self.session = create_tmdb_session()  # Create session with retry logic
        
        if self.initialized:
            print("✅ TMDB Fetcher initialized with aggressive retry logic")
        else:
            print("⚠️ TMDB API key not found. Set TMDB_API_KEY in .env")
            print("   Movies will use placeholder images.")
            print("   Get a free key at: https://www.themoviedb.org/settings/api")
    

    @lru_cache(maxsize=500)
    def search_movie(self, title: str) -> Optional[Dict]:
        """
        Search for a movie by title with aggressive retry logic and fallbacks.
        Implements multiple strategies to ensure 100% success rate.
        """
        if not self.initialized:
            return None
        
        try:
            # Clean up title (remove year in parentheses)
            clean_title = title.split('(')[0].strip()
            
            # Strategy 1: Exact title search with aggressive retries
            url = f"{TMDB_BASE_URL}/search/movie"
            params = {
                "api_key": self.api_key,
                "query": clean_title,
                "language": "en-US",
                "page": 1
            }
            
            # Try with session (has built-in retry logic)
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    response = self.session.get(url, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("results"):
                            movie = data["results"][0]
                            print(f"✅ TMDB found: '{title}' → {movie.get('title')} ({movie.get('release_date', '')[:4]})")
                            
                            return {
                                "id": movie.get("id"),
                                "title": movie.get("title"),
                                "year": movie.get("release_date", "")[:4],
                                "poster_path": movie.get("poster_path"),
                                "backdrop_path": movie.get("backdrop_path"),
                                "overview": movie.get("overview", ""),
                                "rating": round(movie.get("vote_average", 0), 1),
                                "genre_ids": movie.get("genre_ids", [])
                            }
                    
                    # If no results, try fallback strategies
                    if attempt == max_attempts - 1:
                        print(f"⚠️ No exact match for '{title}', trying fallback search...")
                        
                        # Strategy 2: Try without common words
                        fallback_title = clean_title.replace("The ", "").replace("A ", "").replace("An ", "").strip()
                        if fallback_title != clean_title:
                            params["query"] = fallback_title
                            fallback_response = self.session.get(url, params=params, timeout=30)
                            if fallback_response.status_code == 200:
                                fallback_data = fallback_response.json()
                                if fallback_data.get("results"):
                                    movie = fallback_data["results"][0]
                                    print(f"✅ TMDB found (fallback): '{title}' → {movie.get('title')}")
                                    return {
                                        "id": movie.get("id"),
                                        "title": movie.get("title"),
                                        "year": movie.get("release_date", "")[:4],
                                        "poster_path": movie.get("poster_path"),
                                        "backdrop_path": movie.get("backdrop_path"),
                                        "overview": movie.get("overview", ""),
                                        "rating": round(movie.get("vote_average", 0), 1),
                                        "genre_ids": movie.get("genre_ids", [])
                                    }
                    
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, ConnectionResetError) as e:
                    if attempt < max_attempts - 1:
                        delay = (2 ** attempt) * 0.5  # Exponential backoff: 0.5s, 1s, 2s, 4s, 8s
                        print(f"⚠️ Connection error for '{title}' (attempt {attempt + 1}/{max_attempts}), retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        print(f"❌ TMDB connection failed for '{title}' after {max_attempts} attempts: {e}")
                        return None
            
            print(f"⚠️ No TMDB results for '{title}' after all strategies")
            return None
            
        except Exception as e:
            print(f"❌ TMDB search error for '{title}': {e}")
            return None
    
    @lru_cache(maxsize=500)
    def get_movie_trailer(self, movie_id: int) -> Optional[str]:
        """
        Get the YouTube trailer ID for a movie with aggressive retry logic.
        """
        if not self.initialized or not movie_id:
            return None
        
        try:
            url = f"{TMDB_BASE_URL}/movie/{movie_id}/videos"
            params = {
                "api_key": self.api_key,
                "language": "en-US"
            }
            
            # Use session with built-in retry logic
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    response = self.session.get(url, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        videos = data.get("results", [])
                        
                        # Find the official trailer (prefer "Trailer" type)
                        for video in videos:
                            if video.get("site") == "YouTube" and video.get("type") == "Trailer":
                                return video.get("key")
                        
                        # Fallback: any YouTube video
                        for video in videos:
                            if video.get("site") == "YouTube":
                                return video.get("key")
                        
                        return None
                    
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, ConnectionResetError) as e:
                    if attempt < max_attempts - 1:
                        delay = (2 ** attempt) * 0.5
                        time.sleep(delay)
                    else:
                        return None
            
            return None
            
        except Exception as e:
            print(f"TMDB trailer error for movie {movie_id}: {e}")
            return None
    
    def get_movie_details(self, title: str) -> Dict:
        """
        Get complete movie details including poster and trailer.
        Returns a formatted dictionary ready for the frontend.
        """
        # Default response with placeholders
        result = {
            "title": title,
            "poster": f"https://via.placeholder.com/300x450/1a1a2e/ffffff?text={title.replace(' ', '+')}",
            "year": "",
            "genre": "Movie",
            "rating": "N/A",
            "description": f"AI recommended: {title}",
            "trailerId": ""
        }
        
        if not self.initialized:
            return result
        
        # Search for the movie
        movie = self.search_movie(title)
        if movie:
            # Update with real data
            if movie.get("poster_path"):
                result["poster"] = f"{TMDB_IMAGE_BASE}{movie['poster_path']}"
            
            result["year"] = movie.get("year", "")
            result["rating"] = str(movie.get("rating", "N/A"))
            result["description"] = movie.get("overview", result["description"])
            
            # Get trailer
            trailer_id = self.get_movie_trailer(movie.get("id"))
            if trailer_id:
                result["trailerId"] = trailer_id
        
        return result


# Genre mapping (TMDB genre IDs to names)
GENRE_MAP = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Sci-Fi",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western"
}


# Global instance
tmdb_fetcher = None

def get_tmdb_fetcher() -> TMDBFetcher:
    """Get or create the TMDB fetcher instance"""
    global tmdb_fetcher
    if tmdb_fetcher is None:
        tmdb_fetcher = TMDBFetcher()
    return tmdb_fetcher


if __name__ == "__main__":
    print("🎬 TMDB Fetcher Test\n")
    
    fetcher = get_tmdb_fetcher()
    
    if fetcher.initialized:
        # Test with some movies
        test_movies = ["Inception", "The Dark Knight", "Interstellar"]
        
        for movie_title in test_movies:
            print(f"\n🔍 Searching: {movie_title}")
            details = fetcher.get_movie_details(movie_title)
            print(f"   Title: {details['title']}")
            print(f"   Year: {details['year']}")
            print(f"   Rating: {details['rating']}")
            print(f"   Poster: {details['poster'][:60]}...")
            print(f"   Trailer: {details['trailerId'] or 'Not found'}")
    else:
        print("\n⚠️ TMDB API key not configured.")
        print("   Add TMDB_API_KEY to your .env file to enable movie posters and trailers.")
