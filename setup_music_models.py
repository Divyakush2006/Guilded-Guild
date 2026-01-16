"""
Setup script for Pre-trained Music Recommendation System
Installs dependencies and initializes the system
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and print status"""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}")
    try:
        subprocess.check_call(cmd, shell=True)
        print(f"✅ {description} - Complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed: {e}")
        return False

def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║   Music Recommendation System - Pre-trained Models Setup  ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check if we're in venv
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  WARNING: No virtual environment detected!")
        print("   It's recommended to activate your venv first.")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return
    
    print("\n🎯 Installation Plan:")
    print("   1. Install core dependencies (Sentence Transformers, ChromaDB)")
    print("   2. Install audio analysis models (musicnn, librosa)")
    print("   3. Install optional models (panns, CLAP)")
    print("   4. Setup Spotify/YouTube API (manual)")
    print()
    
    # Phase 1: Core dependencies
    print("\n" + "="*60)
    print("PHASE 1: Core Dependencies")
    print("="*60)
    
    core_packages = [
        "sentence-transformers",
        "chromadb",
        "pandas",
        "numpy",
        "scikit-learn"
    ]
    
    for package in core_packages:
        run_command(
            f"{sys.executable} -m pip install {package}",
            f"Installing {package}"
        )
    
    # Phase 2: Audio analysis
    print("\n" + "="*60)
    print("PHASE 2: Audio Analysis Models")
    print("="*60)
    
    print("\nℹ️  Installing musicnn for mood analysis...")
    run_command(
        f"{sys.executable} -m pip install musicnn",
        "Installing musicnn"
    )
    
    print("\nℹ️  Installing librosa for audio processing...")
    run_command(
        f"{sys.executable} -m pip install librosa soundfile",
        "Installing librosa and soundfile"
    )
    
    # Phase 3: Optional models
    print("\n" + "="*60)
    print("PHASE 3: Optional Models (Advanced Features)")
    print("="*60)
    
    print("\nThese models are optional and can be installed later:")
    print("   - panns-inference (Genre classification) ~300MB")
    print("   - laion-clap (Audio similarity) ~600MB")
    print()
    
    install_optional = input("Install optional models now? (y/n): ")
    
    if install_optional.lower() == 'y':
        run_command(
            f"{sys.executable} -m pip install panns-inference",
            "Installing panns-inference"
        )
        
        run_command(
            f"{sys.executable} -m pip install laion-clap",
            "Installing laion-clap"
        )
    else:
        print("⏭️  Skipping optional models. Install later from requirements_music.txt")
    
    # Phase 4: Playback APIs
    print("\n" + "="*60)
    print("PHASE 4: Playback API Setup")
    print("="*60)
    
    print("\n🎵 Choose your playback provider:")
    print("   1. Spotify (spotipy)")
    print("   2. YouTube (google-api-python-client)")
    print("   3. Both")
    print("   4. Skip for now")
    
    choice = input("\nEnter choice (1-4): ")
    
    if choice in ['1', '3']:
        run_command(
            f"{sys.executable} -m pip install spotipy",
            "Installing Spotify API (spotipy)"
        )
    
    if choice in ['2', '3']:
        run_command(
            f"{sys.executable} -m pip install google-api-python-client",
            "Installing YouTube API"
        )
    
    # Summary
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("\n1. Build music dataset:")
    print("   cd flask_app")
    print("   python music_data_fetcher.py")
    
    print("\n2. Initialize embeddings:")
    print("   python inference_music_v2.py")
    
    print("\n3. Configure Spotify/YouTube API:")
    print("   - Get API credentials from Spotify Developer Dashboard")
    print("   - Add credentials to .env file")
    
    print("\n4. Start the server:")
    print("   python app.py")
    
    print("\n📚 Documentation:")
    print("   - Implementation Plan: implementation_plan.md")
    print("   - Quick Start: MUSIC_README.md")
    
    print("\n🎉 Happy music recommending!\n")

if __name__ == "__main__":
    main()
