"""
Main entry point for the Karaoke Automation System
"""

import sys
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils import load_config, setup_logging, ensure_directories
from database import Database, SongStatus
from orchestrator import TrendingOrchestrator
from processor import KaraokeProcessor


def main():
    """Main function"""
    try:
        # Load configuration
        config = load_config()
        
        # Setup logging
        setup_logging(config)
        logger.info("🎤 Karaoke Automation System Started")
        
        # Ensure directories exist
        ensure_directories(config)
        
        # Initialize database
        db = Database(config['paths']['database'])
        
        # Print stats
        stats = db.get_stats()
        logger.info(f"Database stats: {stats['total']} total songs")
        if stats['by_status']:
            for status, count in stats['by_status'].items():
                logger.info(f"  {status}: {count}")
        
        # Main menu
        while True:
            print("\n" + "="*60)
            print("🎤 KARAOKE AUTOMATION SYSTEM")
            print("="*60)
            print("\n1. 🔍 Search for trending songs")
            print("2. 🎵 Process a specific YouTube URL")
            print("3. 📋 Process pending songs")
            print("4. 📊 Show database stats")
            print("5. 🗑️  Clear failed songs")
            print("0. ❌ Exit")
            print()
            
            choice = input("Select option: ").strip()
            
            if choice == '1':
                search_trending(config, db)
            elif choice == '2':
                process_url(config, db)
            elif choice == '3':
                process_pending(config, db)
            elif choice == '4':
                show_stats(db)
            elif choice == '5':
                clear_failed(db)
            elif choice == '0':
                logger.info("Exiting...")
                break
            else:
                print("❌ Invalid option")
    
    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


def search_trending(config, db):
    """Search for trending songs and add to database"""
    try:
        logger.info("Searching for trending songs...")
        orchestrator = TrendingOrchestrator(config, db)
        
        # Get trending songs (don't add yet, show them first)
        trending_songs = orchestrator.search_trending_songs()
        
        if not trending_songs:
            print("\n❌ No trending songs found. Check your API key.")
            return
        
        print(f"\n✅ Found {len(trending_songs)} trending songs in Spain!")
        print("\n" + "="*70)
        print("🔥 TOP TRENDING SONGS IN SPAIN")
        print("="*70 + "\n")
        
        # Show trending songs with details
        for i, song in enumerate(trending_songs[:10], 1):
            views = song.get('view_count', 0)
            views_str = f"{views:,}" if views else "N/A"
            
            # Check if already in database
            exists = db.song_exists(song['youtube_id'])
            status = "✓ In DB" if exists else "New"
            
            print(f"{i:2d}. [{status:6}] {song['title'][:45]:<45}")
            print(f"     Artist: {song['artist'][:35]:<35} | Views: {views_str}")
            print()
        
        print("="*70)
        print("\nOptions:")
        print("  1. Add ALL new songs to database (for batch processing later)")
        print("  2. Select ONE song to process now")
        print("  0. Cancel")
        print()
        
        choice = input("Select option: ").strip()
        
        if choice == '1':
            # Add all new songs to database
            new_count = 0
            for song in trending_songs:
                if not db.song_exists(song['youtube_id']):
                    db.add_song(
                        youtube_id=song['youtube_id'],
                        title=song['title'],
                        url=song['url'],
                        artist=song['artist']
                    )
                    new_count += 1
            
            print(f"\n✅ Added {new_count} new songs to database")
            print(f"   Use option 3 (Process pending songs) to process them")
        
        elif choice == '2':
            # Select one song to process now
            print("\nWhich song? (enter number 1-10)")
            song_num = input("Number: ").strip()
            
            try:
                idx = int(song_num) - 1
                if 0 <= idx < len(trending_songs):
                    selected = trending_songs[idx]
                    
                    # Add to database if not exists
                    if not db.song_exists(selected['youtube_id']):
                        db.add_song(
                            youtube_id=selected['youtube_id'],
                            title=selected['title'],
                            url=selected['url'],
                            artist=selected['artist']
                        )
                    
                    print(f"\n✅ Selected: {selected['title']} - {selected['artist']}")
                    print("\n🎵 Starting processing...\n")
                    
                    # Process immediately
                    processor = KaraokeProcessor(config, db)
                    success = processor.process_song(selected['youtube_id'])
                    
                    if success:
                        song = db.get_song_by_youtube_id(selected['youtube_id'])
                        print("\n✅ Processing completed successfully!")
                        if song['video_path']:
                            print(f"\n📹 Video: {song['video_path']}")
                        if song['youtube_upload_id']:
                            print(f"🔗 YouTube: https://www.youtube.com/watch?v={song['youtube_upload_id']}")
                    else:
                        print("\n❌ Processing failed. Check logs for details.")
                else:
                    print("❌ Invalid number")
            except ValueError:
                print("❌ Invalid input")
        
        else:
            print("⏭️  Cancelled")
    
    except Exception as e:
        logger.error(f"Error searching trending: {e}")
        print(f"❌ Error: {e}")


def process_url(config, db):
    """Process a specific YouTube URL"""
    try:
        from utils import extract_youtube_id
        
        url = input("\nEnter YouTube URL or video ID: ").strip()
        
        if not url:
            print("❌ No URL provided")
            return
        
        # Extract video ID
        try:
            youtube_id = extract_youtube_id(url)
        except ValueError as e:
            print(f"❌ {e}")
            return
        
        # Check if already in database
        existing = db.get_song_by_youtube_id(youtube_id)
        
        if existing:
            print(f"\n⚠️  Song already in database:")
            print(f"  Title: {existing['title']}")
            print(f"  Artist: {existing['artist']}")
            print(f"  Status: {existing['status']}")
            
            if existing['status'] != SongStatus.PENDING:
                reprocess = input("\nReprocess? (y/n): ").strip().lower()
                if reprocess != 'y':
                    return
                
                # Reset to pending
                db.update_status(youtube_id, SongStatus.PENDING)
        else:
            # Fetch video info and add to database
            orchestrator = TrendingOrchestrator(config, db)
            
            # Search for the video
            songs = orchestrator.search_by_query(youtube_id, max_results=1)
            
            if not songs:
                print("❌ Could not fetch video information")
                return
            
            song = songs[0]
            db.add_song(
                youtube_id=song['youtube_id'],
                title=song['title'],
                url=song['url'],
                artist=song['artist']
            )
            
            print(f"\n✅ Added to database:")
            print(f"  Title: {song['title']}")
            print(f"  Artist: {song['artist']}")
        
        # Process the song
        print("\n🎵 Starting processing...")
        processor = KaraokeProcessor(config, db)
        
        success = processor.process_song(youtube_id)
        
        if success:
            print("\n✅ Processing completed successfully!")
            
            # Show result
            song = db.get_song_by_youtube_id(youtube_id)
            if song['video_path']:
                print(f"\n📹 Video: {song['video_path']}")
            if song['youtube_upload_id']:
                print(f"🔗 YouTube: https://www.youtube.com/watch?v={song['youtube_upload_id']}")
        else:
            print("\n❌ Processing failed. Check logs for details.")
    
    except Exception as e:
        logger.error(f"Error processing URL: {e}")
        print(f"❌ Error: {e}")


def process_pending(config, db):
    """Process all pending songs"""
    try:
        pending_songs = db.get_songs_by_status(SongStatus.PENDING)
        
        if not pending_songs:
            print("\n📭 No pending songs to process")
            return
        
        print(f"\n📋 Found {len(pending_songs)} pending songs")
        
        for i, song in enumerate(pending_songs, 1):
            print(f"\n[{i}/{len(pending_songs)}] Processing: {song['title']} - {song['artist']}")
            
            processor = KaraokeProcessor(config, db)
            success = processor.process_song(song['youtube_id'])
            
            if success:
                print(f"  ✅ Success")
            else:
                print(f"  ❌ Failed")
                
                # Ask if should continue
                if i < len(pending_songs):
                    cont = input("\nContinue with next song? (y/n): ").strip().lower()
                    if cont != 'y':
                        break
        
        print("\n✅ Batch processing completed")
    
    except Exception as e:
        logger.error(f"Error processing pending: {e}")
        print(f"❌ Error: {e}")


def show_stats(db):
    """Show database statistics"""
    try:
        stats = db.get_stats()
        
        print("\n" + "="*60)
        print("📊 DATABASE STATISTICS")
        print("="*60)
        print(f"\nTotal songs: {stats['total']}")
        
        if stats['by_status']:
            print("\nBy status:")
            for status, count in sorted(stats['by_status'].items()):
                print(f"  {status:20s}: {count:3d}")
        
        # Show recent songs
        print("\n" + "-"*60)
        print("Recent songs:")
        print("-"*60)
        
        recent = db.get_all_songs(limit=10)
        for song in recent:
            status_emoji = {
                SongStatus.PENDING: "⏳",
                SongStatus.DOWNLOADING: "⬇️",
                SongStatus.SEPARATING: "🔀",
                SongStatus.TRANSCRIBING: "📝",
                SongStatus.GENERATING_VIDEO: "🎬",
                SongStatus.UPLOADING: "⬆️",
                SongStatus.COMPLETED: "✅",
                SongStatus.FAILED: "❌"
            }.get(song['status'], "❓")
            
            print(f"{status_emoji} {song['title']:40s} - {song['artist']:20s} [{song['status']}]")
    
    except Exception as e:
        logger.error(f"Error showing stats: {e}")
        print(f"❌ Error: {e}")


def clear_failed(db):
    """Clear failed songs from database"""
    try:
        failed = db.get_songs_by_status(SongStatus.FAILED)
        
        if not failed:
            print("\n✅ No failed songs to clear")
            return
        
        print(f"\n⚠️  Found {len(failed)} failed songs:")
        for song in failed[:10]:  # Show first 10
            print(f"  - {song['title']} ({song['error_message'][:50] if song['error_message'] else 'No error message'})")
        
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
        
        confirm = input("\nReset all failed songs to pending? (y/n): ").strip().lower()
        
        if confirm == 'y':
            for song in failed:
                db.update_status(song['youtube_id'], SongStatus.PENDING, error_message=None)
            
            print(f"✅ Reset {len(failed)} failed songs to pending status")
        else:
            print("❌ Cancelled")
    
    except Exception as e:
        logger.error(f"Error clearing failed: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
