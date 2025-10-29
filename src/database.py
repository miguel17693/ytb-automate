"""
Database module for tracking processed songs
Uses SQLite to store song metadata and processing status
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from contextlib import contextmanager


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    youtube_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    artist TEXT,
                    url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    download_path TEXT,
                    vocal_path TEXT,
                    instrumental_path TEXT,
                    modified_instrumental_path TEXT,
                    lyrics_path TEXT,
                    video_path TEXT,
                    youtube_upload_id TEXT,
                    error_message TEXT
                )
            """)
            
            # Create index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_youtube_id 
                ON songs(youtube_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON songs(status)
            """)
    
    def add_song(self, youtube_id: str, title: str, url: str, artist: Optional[str] = None) -> int:
        """Add a new song to the database"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO songs (youtube_id, title, artist, url, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (youtube_id, title, artist, url))
            return cursor.lastrowid
    
    def get_song_by_youtube_id(self, youtube_id: str) -> Optional[Dict]:
        """Get song by YouTube ID"""
        with self.get_connection() as conn:
            result = conn.execute("""
                SELECT * FROM songs WHERE youtube_id = ?
            """, (youtube_id,)).fetchone()
            return dict(result) if result else None
    
    def song_exists(self, youtube_id: str) -> bool:
        """Check if song already exists in database"""
        return self.get_song_by_youtube_id(youtube_id) is not None
    
    def update_status(self, youtube_id: str, status: str, error_message: Optional[str] = None):
        """Update song processing status"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE songs 
                SET status = ?, 
                    updated_at = CURRENT_TIMESTAMP,
                    error_message = ?
                WHERE youtube_id = ?
            """, (status, error_message, youtube_id))
    
    def update_paths(self, youtube_id: str, **paths):
        """Update file paths for a song"""
        valid_fields = {
            'download_path', 'vocal_path', 'instrumental_path',
            'modified_instrumental_path', 'lyrics_path', 'video_path',
            'youtube_upload_id'
        }
        
        updates = {k: v for k, v in paths.items() if k in valid_fields}
        if not updates:
            return
        
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [youtube_id]
        
        with self.get_connection() as conn:
            conn.execute(f"""
                UPDATE songs 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE youtube_id = ?
            """, values)
    
    def get_songs_by_status(self, status: str) -> List[Dict]:
        """Get all songs with a specific status"""
        with self.get_connection() as conn:
            results = conn.execute("""
                SELECT * FROM songs WHERE status = ?
                ORDER BY created_at DESC
            """, (status,)).fetchall()
            return [dict(row) for row in results]
    
    def get_all_songs(self, limit: Optional[int] = None) -> List[Dict]:
        """Get all songs, optionally limited"""
        query = "SELECT * FROM songs ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        with self.get_connection() as conn:
            results = conn.execute(query).fetchall()
            return [dict(row) for row in results]
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            stats = {}
            
            # Total songs
            stats['total'] = conn.execute(
                "SELECT COUNT(*) FROM songs"
            ).fetchone()[0]
            
            # By status
            status_counts = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM songs
                GROUP BY status
            """).fetchall()
            
            stats['by_status'] = {row[0]: row[1] for row in status_counts}
            
            return stats


# Status constants
class SongStatus:
    PENDING = "pending"
    DOWNLOADING = "downloading"
    SEPARATING = "separating"
    TRANSCRIBING = "transcribing"
    GENERATING_VIDEO = "generating_video"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
