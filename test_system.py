"""
Quick Test Script - Test system without YouTube upload
Processes a short sample to verify everything works
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils import load_config, setup_logging, ensure_directories
from database import Database
from processor import KaraokeProcessor
from orchestrator import TrendingOrchestrator

def show_menu():
    """Show test menu"""
    print()
    print("="*70)
    print("🧪 SYSTEM TEST - Choose Test Mode")
    print("="*70)
    print()
    print("1. 🔍 Test TRENDING SEARCH (Find popular songs in Spain)")
    print("2. 🎵 Test SPECIFIC URL (Process a specific song)")
    print("0. ❌ Exit")
    print()
    
    choice = input("Select option: ").strip()
    return choice

def test_trending_search(config, db):
    """Test trending search functionality"""
    print()
    print("="*70)
    print("🔍 TESTING TRENDING SEARCH")
    print("="*70)
    print()
    
    orchestrator = TrendingOrchestrator(config, db)
    
    print(f"Searching for trending songs in Spain...")
    print(f"Region: {config['youtube']['region']}")
    print(f"Max results: {config['youtube']['max_results']}")
    print()
    
    try:
        trending_songs = orchestrator.search_trending_songs()
        
        if not trending_songs:
            print("❌ No trending songs found. Check your API key.")
            return None
        
        print(f"✅ Found {len(trending_songs)} trending songs!")
        print()
        print("-"*70)
        print("Top trending songs in Spain:")
        print("-"*70)
        
        for i, song in enumerate(trending_songs[:10], 1):
            views = song.get('view_count', 0)
            views_str = f"{views:,}" if views else "N/A"
            print(f"{i:2d}. {song['title'][:50]:<50}")
            print(f"     Artist: {song['artist'][:40]}")
            print(f"     Views: {views_str}")
            print()
        
        print("-"*70)
        print()
        print("Which song do you want to process?")
        print("Enter number (1-10) or 0 to skip:")
        
        choice = input("Choice: ").strip()
        
        if not choice or choice == '0':
            print("⏭️  Skipping processing")
            return None
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(trending_songs):
                selected_song = trending_songs[idx]
                
                # Add to database if not exists
                if not db.song_exists(selected_song['youtube_id']):
                    db.add_song(
                        youtube_id=selected_song['youtube_id'],
                        title=selected_song['title'],
                        url=selected_song['url'],
                        artist=selected_song['artist']
                    )
                    print(f"✅ Added to database: {selected_song['title']}")
                else:
                    print(f"ℹ️  Already in database: {selected_song['title']}")
                
                return selected_song['youtube_id']
            else:
                print("❌ Invalid choice")
                return None
        except ValueError:
            print("❌ Invalid input")
            return None
    
    except Exception as e:
        print(f"❌ Error searching trending songs: {e}")
        print("Check your YouTube API key in .env")
        return None

def test_specific_url(config, db):
    """Test processing a specific URL"""
    print()
    print("="*70)
    print("🎵 TESTING SPECIFIC URL")
    print("="*70)
    print()
    
    print("Enter a YouTube URL to test (recommend a SHORT song, 2-3 minutes):")
    print("Example: https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    print()
    url = input("YouTube URL: ").strip()
    
    if not url:
        print("❌ No URL provided")
        return None
    
    # Extract video ID
    from utils import extract_youtube_id
    
    try:
        youtube_id = extract_youtube_id(url)
        print(f"✅ Extracted video ID: {youtube_id}")
    except ValueError as e:
        print(f"❌ Invalid URL: {e}")
        return None
    
    # Add to database if not exists
    if not db.song_exists(youtube_id):
        orchestrator = TrendingOrchestrator(config, db)
        songs = orchestrator.search_by_query(youtube_id, max_results=1)
        
        if not songs:
            print("❌ Could not fetch video info")
            return None
        
        song = songs[0]
        db.add_song(
            youtube_id=song['youtube_id'],
            title=song['title'],
            url=song['url'],
            artist=song['artist']
        )
        print(f"✅ Added to database: {song['title']} - {song['artist']}")
    else:
        song = db.get_song_by_youtube_id(youtube_id)
        print(f"ℹ️  Song already in database: {song['title']}")
    
    return youtube_id

def test_system():
    """Quick system test with a sample URL"""
    
    print("="*70)
    print("🧪 QUICK SYSTEM TEST - NO YOUTUBE UPLOAD")
    print("="*70)
    print()
    
    # Load config
    config = load_config()
    setup_logging(config)
    
    # Ensure upload is disabled
    config['upload']['auto_upload'] = False
    
    print("✅ Configuration loaded")
    print(f"   - Region: {config['youtube']['region']} (Spain)")
    print(f"   - Whisper model: {config['audio']['transcription']['model']}")
    print(f"   - YouTube upload: DISABLED ⏭️")
    print()
    
    # Ensure directories
    ensure_directories(config)
    print("✅ Directories ready")
    print()
    
    # Initialize database
    db = Database(config['paths']['database'])
    print("✅ Database ready")
    
    # Show menu
    choice = show_menu()
    
    youtube_id = None
    
    if choice == '1':
        youtube_id = test_trending_search(config, db)
    elif choice == '2':
        youtube_id = test_specific_url(config, db)
    elif choice == '0':
        print("👋 Exiting...")
        return
    else:
        print("❌ Invalid option")
        return
    
    if not youtube_id:
        print("\n⚠️  No song selected for processing")
        return
    
    print()
    print("-"*70)
    print("🎬 STARTING TEST PROCESSING")
    print("-"*70)
    print()
    print("🚀 Processing will now start. This may take several minutes...")
    print("   Watch the logs for progress!")
    print()
    
    # Process
    processor = KaraokeProcessor(config, db)
    success = processor.process_song(youtube_id)
    
    print()
    print("="*70)
    
    if success:
        song = db.get_song_by_youtube_id(youtube_id)
        print("🎉 TEST SUCCESSFUL!")
        print("="*70)
        print()
        print(f"📁 Files generated:")
        print(f"   Audio: {song['download_path']}")
        print(f"   Vocals: {song['vocal_path']}")
        print(f"   Instrumental: {song['instrumental_path']}")
        print(f"   Modified: {song['modified_instrumental_path']}")
        print(f"   Lyrics: {song['lyrics_path']}")
        print(f"   VIDEO: {song['video_path']}")
        print()
        print("📹 You can find your karaoke video at:")
        print(f"   {song['video_path']}")
        print()
        print("✅ System is working correctly!")
        print("   You can now process more songs or enable YouTube upload.")
    else:
        print("❌ TEST FAILED")
        print("="*70)
        print()
        print("Check logs/karaoke.log for details")
        print()
        song = db.get_song_by_youtube_id(youtube_id)
        if song and song['error_message']:
            print(f"Error: {song['error_message']}")
    
    print("="*70)


if __name__ == "__main__":
    try:
        test_system()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
