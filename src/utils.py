"""
Utility functions for the karaoke automation system
"""

import re
import yaml
from pathlib import Path
from typing import Dict, Any
from loguru import logger
import sys


def setup_logging(config: Dict[str, Any]):
    """Configure logging with loguru"""
    log_level = config.get('logging', {}).get('level', 'INFO')
    log_file = config.get('logging', {}).get('file', './logs/karaoke.log')
    
    # Create logs directory
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    # Add console handler with colors
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # Add file handler
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level=log_level,
        rotation="10 MB",
        retention="1 week",
        compression="zip"
    )
    
    return logger


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file"""
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Expand paths to absolute
    if 'paths' in config:
        for key, path in config['paths'].items():
            config['paths'][key] = str(Path(path).resolve())
    
    return config


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters
    """
    # Remove invalid characters for Windows/Unix filesystems
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename


def extract_youtube_id(url: str) -> str:
    """
    Extract YouTube video ID from various URL formats
    
    Supported formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    """
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If no pattern matches, assume it's already an ID
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    
    raise ValueError(f"Could not extract YouTube ID from: {url}")


def format_duration(seconds: float) -> str:
    """Format duration in seconds to HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def clean_artist_name(artist: str) -> str:
    """
    Clean artist name for use in tags/filenames
    Remove feat., vs., and other common additions
    """
    if not artist:
        return ""
    
    # Remove common patterns
    patterns = [
        r'\s*[\(\[].*?feat\..*?[\)\]]',  # (feat. Artist)
        r'\s*[\(\[].*?ft\..*?[\)\]]',    # (ft. Artist)
        r'\s*[\(\[].*?vs\..*?[\)\]]',    # (vs. Artist)
        r'\s*[\(\[].*?x.*?[\)\]]',       # (x Artist)
    ]
    
    cleaned = artist
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned


def generate_video_metadata(song_info: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate optimized title, description, and tags for YouTube upload
    """
    title = song_info.get('title', 'Unknown')
    artist = song_info.get('artist', 'Unknown Artist')
    
    # Clean artist name for tags
    artist_tag = clean_artist_name(artist).replace(' ', '').lower()
    
    metadata = {
        'title': f"{title} - Karaoke (Con Letra)",
        'description': f"""🎤 Karaoke de {title} - {artist}

¡Canta junto a esta versión de karaoke con letras sincronizadas palabra por palabra!

✨ Características:
- Letras sincronizadas en pantalla
- Instrumental de alta calidad
- Resaltado de palabras en tiempo real
- Visualizador de audio

#karaoke #{artist_tag} #musica #letra #cantarkaraoke #karaokeconletra #musicaespañola

---
Video generado automáticamente para uso educativo y de entretenimiento.
""",
        'tags': [
            'karaoke',
            'letra',
            'musica',
            'cantar',
            artist_tag,
            'karaoke con letra',
            'karaoke español',
            title.lower().replace(' ', '')[:20]  # Limit tag length
        ]
    }
    
    return metadata


def ensure_directories(config: Dict[str, Any]):
    """Ensure all required directories exist"""
    paths = config.get('paths', {})
    
    for key, path in paths.items():
        if key != 'database':  # Skip database file
            Path(path).mkdir(parents=True, exist_ok=True)
    
    # Ensure database directory exists
    db_path = Path(paths.get('database', './db/karaoke.db'))
    db_path.parent.mkdir(parents=True, exist_ok=True)


def get_file_size_mb(file_path: str) -> float:
    """Get file size in MB"""
    return Path(file_path).stat().st_size / (1024 * 1024)
