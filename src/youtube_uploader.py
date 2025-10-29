"""
YouTube Uploader - Upload videos to YouTube with metadata
Uses YouTube Data API v3 with OAuth2 authentication
"""

import os
import pickle
from pathlib import Path
from typing import Dict, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from loguru import logger
from dotenv import load_dotenv


class YouTubeUploader:
    """
    Upload videos to YouTube with OAuth2 authentication
    
    Setup:
    1. Create project in Google Cloud Console
    2. Enable YouTube Data API v3
    3. Create OAuth 2.0 credentials (Desktop app)
    4. Download client_secrets.json to project root
    """
    
    # YouTube OAuth scopes
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    
    def __init__(self, config: Dict):
        self.config = config
        self.upload_config = config['upload']
        
        load_dotenv()
        
        # OAuth credentials file
        self.client_secrets_file = 'client_secrets.json'
        self.token_file = 'token.pickle'
        
        self.youtube = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with YouTube using OAuth2"""
        creds = None
        
        # Load saved credentials if they exist
        if Path(self.token_file).exists():
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing YouTube credentials")
                creds.refresh(Request())
            else:
                if not Path(self.client_secrets_file).exists():
                    logger.warning(
                        f"OAuth credentials file not found: {self.client_secrets_file}\n"
                        "YouTube upload will not work until you:\n"
                        "1. Create OAuth credentials in Google Cloud Console\n"
                        "2. Download client_secrets.json to project root"
                    )
                    return
                
                logger.info("Starting OAuth2 flow for YouTube upload")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file,
                    self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next time
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        # Build YouTube service
        self.youtube = build('youtube', 'v3', credentials=creds)
        logger.info("YouTube authentication successful")
    
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list,
        category_id: str = "10",  # Music category
        privacy_status: str = "private"
    ) -> Optional[str]:
        """
        Upload video to YouTube
        
        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            category_id: YouTube category ID (10 = Music)
            privacy_status: public, unlisted, or private
        
        Returns:
            YouTube video ID if successful, None otherwise
        """
        if not self.youtube:
            logger.error("YouTube client not authenticated. Cannot upload video.")
            return None
        
        try:
            logger.info(f"Uploading video to YouTube: {title}")
            
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': title[:100],  # Max 100 characters
                    'description': description[:5000],  # Max 5000 characters
                    'tags': tags[:500],  # Max 500 tags
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Create media upload
            media = MediaFileUpload(
                video_path,
                chunksize=1024*1024,  # 1MB chunks
                resumable=True,
                mimetype='video/mp4'
            )
            
            # Execute upload request
            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            
            response = None
            error = None
            retry = 0
            max_retries = 3
            
            while response is None and retry < max_retries:
                try:
                    logger.info(f"Uploading... (attempt {retry + 1}/{max_retries})")
                    status, response = request.next_chunk()
                    
                    if status:
                        progress = int(status.progress() * 100)
                        logger.info(f"Upload progress: {progress}%")
                
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504]:
                        # Retry on server errors
                        error = f"Server error: {e.resp.status}"
                        retry += 1
                        logger.warning(f"{error}, retrying...")
                    else:
                        raise
            
            if response:
                video_id = response['id']
                logger.info(f"Video uploaded successfully! ID: {video_id}")
                logger.info(f"Watch at: https://www.youtube.com/watch?v={video_id}")
                return video_id
            else:
                logger.error(f"Upload failed after {max_retries} attempts: {error}")
                return None
        
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error uploading video: {e}")
            return None
    
    def upload_karaoke_video(
        self,
        video_path: str,
        song_info: Dict,
        custom_metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Upload karaoke video with auto-generated metadata
        
        Args:
            video_path: Path to video file
            song_info: Dictionary with song information (title, artist, etc.)
            custom_metadata: Optional custom metadata overrides
        
        Returns:
            YouTube video ID if successful
        """
        from utils import generate_video_metadata
        
        # Generate metadata
        metadata = generate_video_metadata(song_info)
        
        # Apply custom overrides if provided
        if custom_metadata:
            metadata.update(custom_metadata)
        
        # Get privacy status from config
        privacy_status = self.upload_config.get('privacy_status', 'private')
        
        # Upload
        return self.upload_video(
            video_path=video_path,
            title=metadata['title'],
            description=metadata['description'],
            tags=metadata['tags'],
            privacy_status=privacy_status
        )
    
    def check_upload_enabled(self) -> bool:
        """Check if auto-upload is enabled in config"""
        return self.upload_config.get('auto_upload', False)


if __name__ == "__main__":
    # Test the uploader
    from utils import load_config, setup_logging
    
    config = load_config()
    setup_logging(config)
    
    uploader = YouTubeUploader(config)
    
    print("YouTube uploader module loaded")
    print(f"Auto-upload enabled: {uploader.check_upload_enabled()}")
    print(f"Authenticated: {uploader.youtube is not None}")
