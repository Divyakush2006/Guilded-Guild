"""
Complete Music Dataset Builder
Audius (English, filtered) + iTunes (Hindi/Bollywood)
100% FREE - No API keys required!
"""

import pandas as pd
from music_data_fetcher import AudiusMusicFetcher
from itunes_fetcher import iTunesFetcher

def build_complete_dataset():
    """Build dataset with both English and Hindi songs"""
    print("=" * 60)
    print("🎵 Building Complete Music Dataset")
    print("   Audius (English) + iTunes (Hindi)")
    print("=" * 60)
    
    # Step 1: Fetch Audius tracks (English, filtered)
    print("\n📊 Step 1: Fetching English tracks from Audius...")
    audius = AudiusMusicFetcher()
    audius_df = audius.build_dataset(
        num_trending=150,
        filter_playlists=False  # Include BOTH songs and playlists
    )
    
    # Step 2: Fetch Hindi tracks from iTunes
    print("\n📊 Step 2: Fetching Hindi/Bollywood tracks from iTunes...")
    itunes = iTunesFetcher()
    hindi_tracks = itunes.get_hindi_songs(num_tracks=200)
    itunes_df = pd.DataFrame(hindi_tracks)
    
    # Step 3: Combine datasets
    print("\n🔧 Step 3: Merging datasets...")
    combined_df = pd.concat([audius_df, itunes_df], ignore_index=True)
    
    # Show summary
    print("\n" + "=" * 60)
    print("📊 Dataset Summary:")
    print("=" * 60)
    print(f"   Audius (English):     {len(audius_df)} tracks")
    print(f"   iTunes (Hindi):       {len(itunes_df)} tracks")
    print(f"   ─────────────────────")
    print(f"   TOTAL:                {len(combined_df)} tracks")
    print("=" * 60)
    
    # Show genre breakdown
    print("\n📋 Genre Distribution:")
    genre_counts = combined_df['genre'].value_counts().head(10)
    for genre, count in genre_counts.items():
        print(f"   {genre}: {count}")
    
    # Show sample Hindi tracks
    print("\n🎵 Sample Hindi Tracks:")
    hindi_samples = combined_df[combined_df['genre'].str.contains('Bollywood|Indian|Hindi', case=False, na=False)]
    for i, row in hindi_samples.head(5).iterrows():
        print(f"   • {row['title']} - {row['artist']}")
    
    # Save dataset
    print("\n💾 Saving dataset...")
    audius.save_dataset(combined_df, "music_dataset.pkl")
    audius.create_encoders(combined_df)
    
    print("\n✅ Dataset build complete!")
    print("\n🔧 Next steps:")
    print("   1. Delete old vector database:")
    print("      Remove-Item -Recurse -Force music_vectordb")
    print("   2. Rebuild embeddings:")
    print("      python inference_music_v2.py")
    print("   3. Restart Flask server")
    
    return combined_df

if __name__ == "__main__":
    df = build_complete_dataset()
