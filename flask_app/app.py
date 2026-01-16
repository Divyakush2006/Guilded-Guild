from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from inference_sasrec import rec_engine
import time  # For rate limiting TMDB requests 

# Import Spotify-based music recommender (uses real Spotify API)
try:
    from spotify_recommender import initialize_spotify_recommender
    music_engine = initialize_spotify_recommender()
    MUSIC_ENABLED = music_engine is not None and music_engine.initialized
except Exception as e:
    print(f"⚠️ Spotify music recommender not available: {e}")
    MUSIC_ENABLED = False
    music_engine = None

# Import TMDB fetcher for movie posters and trailers
try:
    from tmdb_fetcher import get_tmdb_fetcher
    tmdb = get_tmdb_fetcher()
except Exception as e:
    print(f"⚠️ TMDB fetcher not available: {e}")
    # Fallback - create a dummy object
    class DummyTMDB:
        def get_movie_details(self, title):
            return {
                'poster': f"https://via.placeholder.com/300x450/1a1a2e/ffffff?text={title.replace(' ', '+')}",
                'year': '', 'genre': 'Movie', 'rating': 'N/A',
                'description': f'AI recommended: {title}', 'trailerId': ''
            }
    tmdb = DummyTMDB()

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# ============================================
# HTML Template Routes (Legacy)
# ============================================

@app.route('/')
def home():
    return render_template('index.html', music_enabled=MUSIC_ENABLED)

@app.route('/music')
def music_page():
    """Music recommendation page"""
    return render_template('music.html', spotify_enabled=MUSIC_ENABLED)

@app.route('/recommend', methods=['POST']) 
def recommend():
    try:
        current_watch = request.form.get('current_watch', '').strip()
        history_raw = request.form.get('history', '').strip()

        user_movies = []
        if history_raw:
            user_movies.extend([m.strip() for m in history_raw.split(',')])
        
        if current_watch:
            user_movies.append(current_watch)

        if not user_movies:
            return render_template('index.html', error="Please enter at least one movie.")

        print(f"🧠 Processing: {user_movies}")
        raw_recs = rec_engine.predict(user_movies)
        
        recs_data = {
            'current_context': raw_recs[:5],
            'history_based': raw_recs[5:10],
            'debug_info': [
                f"Input sequence: {user_movies}",
                f"Model used: SASRec (Epoch 20)",
                f"Raw top prediction: {raw_recs[0] if raw_recs else 'None'}"
            ]
        }
        
        return render_template('index.html', recs=recs_data)

    except Exception as e:
        print(f"Error: {e}")
        return render_template('index.html', error=str(e))

@app.route('/recommend_music', methods=['POST'])
def recommend_music():
    """Music recommendation endpoint - uses Spotify API for REAL songs"""
    if not MUSIC_ENABLED:
        return render_template('music.html', 
            error="Spotify not configured. Please run: python setup_spotify.py",
            spotify_enabled=False
        )
    
    try:
        current_track = request.form.get('current_track', '').strip()
        history_raw = request.form.get('history', '').strip()
        
        history = []
        if history_raw:
            history = [t.strip() for t in history_raw.split(',') if t.strip()]
        
        if not current_track:
            return render_template('music.html', 
                error="Please enter a song name.",
                spotify_enabled=MUSIC_ENABLED
            )
        
        print(f"🎵 Finding similar songs for: {current_track}")
        if history:
            print(f"   With history: {history}")
        
        similar_tracks = music_engine.predict(current_track, history)
        
        recs_data = {
            'similar_tracks': similar_tracks,
            'input_track': current_track,
            'input_history': history,
            'debug_info': [
                f"Current track: {current_track}",
                f"History tracks: {len(history)}",
                f"Engine: Spotify Recommendations API",
                f"Similar songs found: {len(similar_tracks)}"
            ]
        }
        
        return render_template('music.html', recs=recs_data, spotify_enabled=MUSIC_ENABLED)
    
    except Exception as e:
        print(f"Music Error: {e}")
        import traceback
        traceback.print_exc()
        return render_template('music.html', error=str(e), spotify_enabled=MUSIC_ENABLED)


# ============================================
# JSON API Routes (for React Frontend)
# ============================================

@app.route('/api/recommend/movies', methods=['POST'])
def api_recommend_movies():
    """JSON API for movie recommendations with TMDB metadata"""
    try:
        data = request.get_json() or {}
        current_watch = data.get('current', '').strip()
        history_raw = data.get('history', '').strip()

        user_movies = []
        if history_raw:
            user_movies.extend([m.strip() for m in history_raw.split(',')])
        
        if current_watch:
            user_movies.append(current_watch)

        if not user_movies:
            return jsonify({'error': 'Please enter at least one movie.'}), 400

        print(f"🧠 [API] Processing movies: {user_movies}")
        raw_recs = rec_engine.predict(user_movies)
        
        # Format recommendations with TMDB metadata (poster + trailer)
        def format_movie(title: str) -> dict:
            # Get real movie data from TMDB
            print(f"🎬 [TMDB] Fetching details for: {title}")
            details = tmdb.get_movie_details(title)
            print(f"   Poster: {details.get('poster', '')[:60]}...")
            print(f"   Trailer ID: {details.get('trailerId', 'None')}")
            
            # Increased delay to prevent overwhelming TMDB API and reduce connection errors
            time.sleep(0.5)
            
            return {
                'id': title.lower().replace(' ', '-').replace(',', ''),
                'title': title,
                'poster': details.get('poster', ''),
                'year': details.get('year', ''),
                'genre': details.get('genre', 'Movie'),
                'rating': details.get('rating', 'N/A'),
                'description': details.get('description', f'AI recommended: {title}'),
                'trailerId': details.get('trailerId', '')
            }
        
        return jsonify({
            'success': True,
            'current_context': [format_movie(m) for m in raw_recs[:5]],
            'history_based': [format_movie(m) for m in raw_recs[5:10]],
            'input': {
                'current': current_watch,
                'history': history_raw
            }
        })

    except Exception as e:
        print(f"API Movie Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/recommend/music', methods=['POST'])
def api_recommend_music():
    """JSON API for music recommendations"""
    if not MUSIC_ENABLED:
        return jsonify({
            'error': 'Spotify not configured. Please run: python setup_spotify.py',
            'spotify_enabled': False
        }), 503
    
    try:
        data = request.get_json() or {}
        current_track = data.get('current', '').strip()
        history_raw = data.get('history', '').strip()
        
        history = []
        if history_raw:
            history = [t.strip() for t in history_raw.split(',') if t.strip()]
        
        if not current_track:
            return jsonify({'error': 'Please enter a song name.'}), 400
        
        print(f"🎵 [API] Finding similar songs for: {current_track}")
        if history:
            print(f"   With history: {history}")
        
        similar_tracks = music_engine.predict(current_track, history)
        
        # Format songs for React frontend
        formatted_tracks = []
        for track in similar_tracks:
            formatted_tracks.append({
                'id': track.get('title', '').lower().replace(' ', '-'),
                'title': track.get('title', 'Unknown'),
                'artist': track.get('artist', 'Unknown Artist'),
                'album': track.get('album', 'Unknown Album'),
                'artwork': track.get('artwork_url', ''),
                'spotifyUrl': track.get('spotify_url', 'https://open.spotify.com'),
                'duration': ''
            })
        
        return jsonify({
            'success': True,
            'recommendations': formatted_tracks,
            'input': {
                'current': current_track,
                'history': history
            }
        })
    
    except Exception as e:
        print(f"API Music Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def api_status():
    """Health check and status endpoint"""
    return jsonify({
        'status': 'ok',
        'movie_engine': 'SASRec',
        'music_engine': 'Spotify' if MUSIC_ENABLED else 'Not Configured',
        'music_enabled': MUSIC_ENABLED
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)