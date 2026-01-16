"""
Interactive Spotify Setup Script
Helps you configure Spotify API credentials easily
"""

import os

def setup_spotify_credentials():
    """Interactive setup for Spotify credentials"""
    print("=" * 60)
    print("🎵 Spotify API Setup")
    print("=" * 60)
    
    print("\n📝 Steps to get your Spotify credentials:")
    print("1. Open browser at: https://developer.spotify.com/dashboard")
    print("2. Log in with your Spotify account (FREE)")
    print("3. Click 'Create app'")
    print("4. Fill in:")
    print("   - App name: Music Recommender")
    print("   - App description: AI Music Recommendation")
    print("   - Redirect URI: http://localhost:8888/callback")
    print("5. Click 'Settings' → View your Client ID and Client Secret")
    
    print("\n" + "=" * 60)
    print("Enter your Spotify credentials:")
    print("=" * 60)
    
    client_id = input("\n📌 Spotify Client ID: ").strip()
    client_secret = input("📌 Spotify Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("\n❌ Error: Both credentials are required!")
        return False
    
    # Create .env file
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    
    with open(env_path, 'w') as f:
        f.write(f"# Spotify API Credentials\n")
        f.write(f"SPOTIFY_CLIENT_ID={client_id}\n")
        f.write(f"SPOTIFY_CLIENT_SECRET={client_secret}\n")
    
    print(f"\n✅ Credentials saved to: {env_path}")
    
    # Test connection
    print("\n🧪 Testing Spotify connection...")
    try:
        from spotify_fetcher import SpotifyHindiFetcher
        
        fetcher = SpotifyHindiFetcher()
        tracks = fetcher.search_hindi_songs("Arijit Singh", limit=5)
        
        if tracks:
            print("✅ Spotify connection successful!")
            print(f"   Found {len(tracks)} test tracks")
            print("\nSample tracks:")
            for i, track in enumerate(tracks[:3], 1):
                print(f"   {i}. {track['title']} - {track['artist']}")
            return True
        else:
            print("⚠️ Connection successful but no tracks found")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("   Please check your credentials and try again")
        return False

if __name__ == "__main__":
    success = setup_spotify_credentials()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 Setup Complete!")
        print("=" * 60)
        print("\nNext step: Run the dataset builder")
        print("   cd flask_app")
        print("   python build_music_dataset.py")
        print("   (Choose option 2 for Audius + Spotify)")
    else:
        print("\n" + "=" * 60)
        print("⚠️ Setup Incomplete")
        print("=" * 60)
        print("\nPlease try again with correct credentials")
