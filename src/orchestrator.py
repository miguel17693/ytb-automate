"""
Orchestrator - Searches for trending songs on YouTube
"""

import os
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger
from dotenv import load_dotenv

from database import Database, SongStatus
from utils import extract_youtube_id


class TrendingOrchestrator:
    def __init__(self, config: Dict, db: Database):
        self.config = config
        self.db = db
        
        # Load environment variables
        load_dotenv()
        
        # Get API key from environment or config
        self.api_key = os.getenv('YOUTUBE_API_KEY') or config['youtube'].get('api_key')
        if not self.api_key:
            raise ValueError("YouTube API key not found in .env or config.yaml")
        
        # Initialize YouTube API client
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        
        # Configuration
        self.region = config['youtube']['region']
        self.max_results = config['youtube']['max_results']
        self.category_id = str(config['youtube']['category_id'])
    
    def search_trending_songs(self) -> List[Dict]:
        """
        Search for trending music videos in the configured region
        Returns list of video info dictionaries
        """
        try:
            logger.info(f"Searching for trending songs in region: {self.region}")
            
            # Use videos().list() to get popular videos in the Music category
            request = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                chart='mostPopular',
                regionCode=self.region,
                videoCategoryId=self.category_id,
                maxResults=self.max_results
            )
            
            response = request.execute()
            
            trending_songs = []
            for item in response.get('items', []):
                video_info = self._parse_video_item(item)
                if video_info:
                    trending_songs.append(video_info)
            
            logger.info(f"Found {len(trending_songs)} trending songs")
            return trending_songs
        
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching trending songs: {e}")
            return []
    
    def search_by_query(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search for songs by query string
        Useful for finding specific trending songs or artists
        """
        try:
            logger.info(f"Searching YouTube for: {query}")
            
            request = self.youtube.search().list(
                part='snippet',
                q=query,
                type='video',
                videoCategoryId=self.category_id,
                maxResults=max_results,
                regionCode=self.region,
                order='viewCount'  # Order by view count
            )
            
            response = request.execute()
            
            songs = []
            for item in response.get('items', []):
                video_id = item['id']['videoId']
                
                # Get full video details
                video_request = self.youtube.videos().list(
                    part='snippet,contentDetails,statistics',
                    id=video_id
                )
                video_response = video_request.execute()
                
                if video_response.get('items'):
                    video_info = self._parse_video_item(video_response['items'][0])
                    if video_info:
                        songs.append(video_info)
            
            logger.info(f"Found {len(songs)} songs matching query: {query}")
            return songs
        
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching by query: {e}")
            return []
    
    def _parse_video_item(self, item: Dict) -> Optional[Dict]:
        """Parse YouTube API video item into our format"""
        try:
            video_id = item['id']
            snippet = item['snippet']
            
            # Extract title and try to parse artist
            title = snippet['title']
            channel_title = snippet['channelTitle']
            
            # Try to extract artist from title (common formats: "Artist - Song" or "Song - Artist")
            artist = self._extract_artist_from_title(title, channel_title)
            
            video_info = {
                'youtube_id': video_id,
                'title': title,
                'artist': artist,
                'channel': channel_title,
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'thumbnail': snippet['thumbnails']['high']['url'],
                'published_at': snippet['publishedAt'],
                'view_count': int(item.get('statistics', {}).get('viewCount', 0)),
                'like_count': int(item.get('statistics', {}).get('likeCount', 0)),
            }
            
            return video_info
        
        except Exception as e:
            logger.warning(f"Error parsing video item: {e}")
            return None
    
    def _extract_artist_from_title(self, title: str, channel: str) -> str:
        """
        Try to extract artist name from video title
        Common patterns:
        - "Artist - Song Title"
        - "Song Title - Artist"
        - Use channel name as fallback
        """
        # Remove common suffixes
        title_clean = title.lower()
        for suffix in ['(official video)', '(official music video)', '(lyric video)', 
                       '(audio)', '[official video]', '(vevo)', '(official audio)']:
            title_clean = title_clean.replace(suffix, '')
        
        title_clean = title_clean.strip()
        
        # Try to split by dash
        if ' - ' in title_clean:
            parts = title_clean.split(' - ', 1)
            # First part is usually the artist
            return parts[0].strip().title()
        
        # Fallback to channel name
        return channel
    
    def process_trending_songs(self) -> int:
        """
        Main method: Find trending songs and add new ones to database
        Returns number of new songs added
        """
        trending_songs = self.search_trending_songs()
        
        new_songs_count = 0
        
        for song in trending_songs:
            youtube_id = song['youtube_id']
            
            # Check if already in database
            if self.db.song_exists(youtube_id):
                logger.debug(f"Song already in database: {song['title']}")
                continue
            
            # Add to database with pending status
            try:
                self.db.add_song(
                    youtube_id=youtube_id,
                    title=song['title'],
                    url=song['url'],
                    artist=song['artist']
                )
                logger.info(f"Added new trending song: {song['title']} - {song['artist']}")
                new_songs_count += 1
            
            except Exception as e:
                logger.error(f"Error adding song to database: {e}")
        
        logger.info(f"Added {new_songs_count} new trending songs to database")
        return new_songs_count
    
    def get_pending_songs(self) -> List[Dict]:
        """Get all songs with pending status from database"""
        return self.db.get_songs_by_status(SongStatus.PENDING)


if __name__ == "__main__":
    # Test the orchestrator
    from utils import load_config, setup_logging
    
    config = load_config()
    setup_logging(config)
    
    db = Database(config['paths']['database'])
    orchestrator = TrendingOrchestrator(config, db)
    
    # Test trending search
    new_songs = orchestrator.process_trending_songs()
    print(f"\nAdded {new_songs} new trending songs")
    
    # Show pending songs
    pending = orchestrator.get_pending_songs()
    print(f"\nPending songs: {len(pending)}")
    for song in pending[:5]:  # Show first 5
        print(f"  - {song['title']} ({song['artist']})")
