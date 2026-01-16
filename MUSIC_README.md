# 🎵 Music Recommendation System - Quick Start Guide

## What's Been Built

You now have a **dual recommendation system**:
- 🎬 **Movie Recommendations** (MovieLens-25M dataset)
- 🎵 **Music Recommendations** (Audius API - completely free!)

## First Time Setup

### Step 1: Build the Music Dataset
```bash
cd flask_app
python music_data_fetcher.py
```

This will:
- Fetch ~500 trending tracks from Audius
- Search additional tracks across popular genres
- Create encoders and save dataset files
- Takes about 2-3 minutes

**Expected output:**
```
📊 Fetching 200 trending tracks...
✅ Fetched 200 trending tracks
📊 Fetching tracks from 13 genres...
🔧 Processing tracks...
✅ Dataset ready: XXX unique tracks
💾 Saved dataset to music_dataset.pkl
✅ Created encoders:
   - Tracks: XXX unique tracks
   - Artists: XXX unique artists
```

### Step 2: Test the Integration
```bash
python test_music_integration.py
```

This verifies:
- ✅ Data fetcher works
- ✅ Music engine initializes
- ✅ Flask routes are configured
- ✅ Dataset files exist

### Step 3: Start the Server
```bash
python app.py
```

Server runs on: `http://localhost:5000`

## Using the System

### Movies (Existing Feature)
1. Go to `http://localhost:5000/`
2. Enter a movie you're watching (e.g., "Iron Man")
3. Optionally add watch history (e.g., "Toy Story, Shrek")
4. Click "Generate Recommendations"

### Music (New Feature!)
1. Go to `http://localhost:5000/music`
2. Enter a track you're listening to (e.g., "Phony")
3. Optionally add listening history (e.g., "Latch, Hold On")
4. Click "Generate Music Recommendations"
5. **Play music directly in the browser!** 🎧

## Sample Tracks to Try

Based on Audius trending data, try these:
- **Dubstep/Bass:** Phony, TUNER'S GROOVE, Hold On
- **House:** Latch, Never, Summer Beach
- **Electronic:** Explore With Us, Level, OK
- **Pop:** Two Boys in California
- **Jazz:** Silver Flame

## How It Works

### API Fallback Mode (Current)
Since no trained model exists yet:
- Uses **Audius API** directly for recommendations
- Matches genre from your input track
- Returns trending/similar tracks in that genre
- **No authentication needed** - completely free!

### Future: Model-Based Mode
Once you train a model:
- Uses **SASRec** (same architecture as movies)
- Learns your listening patterns
- Provides personalized predictions

## Architecture

```
User Input → inference_music.py → [Model OR API Fallback] → Recommendations
                ↓
         music_data_fetcher.py (builds dataset)
                ↓
         Audius API (https://api.audius.co/v1)
```

## Files Created

| File | Purpose |
|------|---------|
| `music_data_fetcher.py` | Fetches music from Audius API |
| `inference_music.py` | Recommendation engine |
| `templates/music.html` | Music UI with audio player |
| `test_music_integration.py` | Verification script |
| `music_dataset.pkl` | Music metadata (created on first run) |
| `track_encoder.pkl` | Track ID encoder |
| `artist_encoder.pkl` | Artist encoder |

## Troubleshooting

### "Music recommender not available"
**Solution:** Run `python music_data_fetcher.py` first

### "No recommendations found"
**Possible causes:**
1. Track name not in dataset → Try more popular tracks
2. API fallback mode → Still works, uses genre matching
3. Network issue → Check internet connection

### Audio won't play
**Possible causes:**
1. Browser doesn't support HTML5 audio → Try Chrome/Firefox
2. Track stream URL expired → Refresh page and try again
3. Audius API temporarily down → Wait and retry

## API Information

**Audius API:**
- **Base URL:** https://api.audius.co/v1
- **Authentication:** None required (just add `app_name` parameter)
- **Rate Limits:** None - unlimited requests!
- **Documentation:** https://docs.audius.org/api

**Key Endpoints Used:**
- `/tracks/trending` - Get popular tracks
- `/tracks/search?query={term}` - Search tracks
- `/tracks/{id}/stream` - Stream audio

## Next Steps

1. **Train a Music Model** (Optional)
   - Collect user interaction data
   - Train SASRec on music sequences
   - Save as `sasrec_music.pth`

2. **Expand Dataset**
   - Fetch more genres
   - Increase trending track count
   - Add user interaction tracking

3. **Enhance UI**
   - Add playlists
   - Save favorites
   - Share recommendations

## Support

If you encounter issues:
1. Check the terminal logs for error messages
2. Run `python test_music_integration.py` for diagnostics
3. Verify dataset files exist in `flask_app/` directory

Enjoy your music recommendations! 🎵🚀
