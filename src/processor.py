"""
Processor - Main processing pipeline for karaoke generation
Orchestrates: Download → Separation → Modification → Transcription → Video → Upload
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
import yt_dlp
import whisper

from database import Database, SongStatus
from audio_modifier import AudioModifier
from lyrics_generator import LyricsGenerator
from video_generator import VideoGenerator
from youtube_uploader import YouTubeUploader
from utils import sanitize_filename, get_file_size_mb


class KaraokeProcessor:
    def __init__(self, config: Dict, db: Database):
        self.config = config
        self.db = db
        self.paths = config['paths']
        
        # Initialize modules
        self.audio_modifier = AudioModifier(config)
        self.lyrics_generator = LyricsGenerator(config)
        self.video_generator = VideoGenerator(config)
        self.youtube_uploader = YouTubeUploader(config)
        
        # Load Whisper model
        whisper_model = config['audio']['transcription']['model']
        logger.info(f"Loading Whisper model: {whisper_model}")
        self.whisper_model = whisper.load_model(whisper_model)
        
        # Spleeter settings
        self.separation_model = config['audio']['separation']['model']
    
    def process_song(self, youtube_id: str) -> bool:
        """
        Process a song through the complete pipeline
        
        Args:
            youtube_id: YouTube video ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get song info from database
            song = self.db.get_song_by_youtube_id(youtube_id)
            if not song:
                logger.error(f"Song not found in database: {youtube_id}")
                return False
            
            logger.info(f"Processing song: {song['title']} - {song['artist']}")
            
            # Step 1: Download audio
            audio_path = self._download_audio(song)
            if not audio_path:
                return False
            
            # Step 2: Separate vocals and instrumental
            vocal_path, instrumental_path = self._separate_audio(song, audio_path)
            if not vocal_path or not instrumental_path:
                return False
            
            # Step 3: Modify instrumental (subtle changes)
            modified_instrumental = self._modify_instrumental(song, instrumental_path)
            if not modified_instrumental:
                return False
            
            # Step 4: Transcribe vocals to get lyrics
            lyrics_srt_path = self._transcribe_vocals(song, vocal_path)
            if not lyrics_srt_path:
                return False
            
            # Step 5: Convert SRT to ASS karaoke format
            lyrics_ass_path = self._generate_ass_lyrics(song, lyrics_srt_path)
            if not lyrics_ass_path:
                return False
            
            # Step 6: Generate karaoke video
            video_path = self._generate_video(song, modified_instrumental, lyrics_ass_path)
            if not video_path:
                return False
            
            # Step 7: Upload to YouTube (if enabled)
            youtube_video_id = self._upload_to_youtube(song, video_path)
            
            # Mark as completed
            self.db.update_status(youtube_id, SongStatus.COMPLETED)
            
            logger.info("="*60)
            logger.info(f"✅ Successfully processed: {song['title']}")
            logger.info("="*60)
            logger.info(f"📹 Local video: {video_path}")
            if youtube_video_id:
                logger.info(f"🔗 YouTube: https://www.youtube.com/watch?v={youtube_video_id}")
            else:
                logger.info("⏭️  Not uploaded to YouTube (upload disabled)")
            logger.info("="*60)
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing song {youtube_id}: {e}")
            self.db.update_status(youtube_id, SongStatus.FAILED, str(e))
            return False
    
    def _download_audio(self, song: Dict) -> Optional[str]:
        """Download audio from YouTube"""
        try:
            self.db.update_status(song['youtube_id'], SongStatus.DOWNLOADING)
            logger.info(f"Downloading audio: {song['url']}")
            
            # Create safe filename
            safe_title = sanitize_filename(f"{song['artist']} - {song['title']}")
            output_path = Path(self.paths['downloads']) / f"{safe_title}_{song['youtube_id']}.wav"
            
            # yt-dlp options
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(output_path.with_suffix('')),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                }],
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([song['url']])
            
            if not output_path.exists():
                raise FileNotFoundError(f"Downloaded file not found: {output_path}")
            
            logger.info(f"Audio downloaded: {output_path.name} ({get_file_size_mb(output_path):.1f} MB)")
            
            # Update database
            self.db.update_paths(song['youtube_id'], download_path=str(output_path))
            
            return str(output_path)
        
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            return None
    
    def _separate_audio(self, song: Dict, audio_path: str) -> tuple[Optional[str], Optional[str]]:
        """Separate vocals and instrumental using Spleeter"""
        try:
            self.db.update_status(song['youtube_id'], SongStatus.SEPARATING)
            logger.info("Separating vocals and instrumental")
            
            output_dir = Path(self.paths['processed']) / song['youtube_id']
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if self.separation_model == 'spleeter':
                # Use Spleeter command line
                cmd = [
                    'spleeter',
                    'separate',
                    '-p', 'spleeter:2stems',  # 2 stems: vocals + accompaniment
                    '-o', str(output_dir.parent),
                    audio_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                
                if result.returncode != 0:
                    logger.error(f"Spleeter error: {result.stderr}")
                    raise RuntimeError("Spleeter separation failed")
                
                # Spleeter outputs to: output_dir/<filename>/vocals.wav and accompaniment.wav
                audio_name = Path(audio_path).stem
                spleeter_output_dir = output_dir.parent / audio_name
                
                vocal_path = spleeter_output_dir / 'vocals.wav'
                instrumental_path = spleeter_output_dir / 'accompaniment.wav'
                
                if not vocal_path.exists() or not instrumental_path.exists():
                    raise FileNotFoundError("Spleeter output files not found")
                
                # Move to our organized directory
                final_vocal_path = output_dir / 'vocals.wav'
                final_instrumental_path = output_dir / 'instrumental.wav'
                
                vocal_path.rename(final_vocal_path)
                instrumental_path.rename(final_instrumental_path)
                
                # Clean up spleeter directory
                if spleeter_output_dir.exists():
                    import shutil
                    shutil.rmtree(spleeter_output_dir)
                
                vocal_path = final_vocal_path
                instrumental_path = final_instrumental_path
            
            else:
                raise NotImplementedError(f"Separation model not implemented: {self.separation_model}")
            
            logger.info(f"Audio separated successfully")
            logger.info(f"  Vocals: {get_file_size_mb(vocal_path):.1f} MB")
            logger.info(f"  Instrumental: {get_file_size_mb(instrumental_path):.1f} MB")
            
            # Update database
            self.db.update_paths(
                song['youtube_id'],
                vocal_path=str(vocal_path),
                instrumental_path=str(instrumental_path)
            )
            
            return str(vocal_path), str(instrumental_path)
        
        except Exception as e:
            logger.error(f"Error separating audio: {e}")
            return None, None
    
    def _modify_instrumental(self, song: Dict, instrumental_path: str) -> Optional[str]:
        """Apply subtle modifications to instrumental"""
        try:
            logger.info("Modifying instrumental")
            
            output_dir = Path(self.paths['processed']) / song['youtube_id']
            modified_path = output_dir / 'instrumental_modified.wav'
            
            result_path = self.audio_modifier.modify_instrumental(
                instrumental_path,
                str(modified_path)
            )
            
            logger.info(f"Instrumental modified: {get_file_size_mb(result_path):.1f} MB")
            
            # Update database
            self.db.update_paths(
                song['youtube_id'],
                modified_instrumental_path=result_path
            )
            
            return result_path
        
        except Exception as e:
            logger.error(f"Error modifying instrumental: {e}")
            return None
    
    def _transcribe_vocals(self, song: Dict, vocal_path: str) -> Optional[str]:
        """Transcribe vocals using Whisper"""
        try:
            self.db.update_status(song['youtube_id'], SongStatus.TRANSCRIBING)
            logger.info("Transcribing vocals with Whisper")
            
            language = self.config['audio']['transcription']['language']
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(
                vocal_path,
                language=language,
                task='transcribe',
                verbose=False
            )
            
            # Save as SRT
            output_dir = Path(self.paths['processed']) / song['youtube_id']
            srt_path = output_dir / 'lyrics.srt'
            
            # Convert Whisper output to SRT format
            self._save_whisper_as_srt(result, str(srt_path))
            
            logger.info(f"Lyrics transcribed: {len(result['segments'])} segments")
            
            return str(srt_path)
        
        except Exception as e:
            logger.error(f"Error transcribing vocals: {e}")
            return None
    
    def _save_whisper_as_srt(self, whisper_result: Dict, output_path: str):
        """Convert Whisper result to SRT format"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(whisper_result['segments'], start=1):
                start_time = self._seconds_to_srt_time(segment['start'])
                end_time = self._seconds_to_srt_time(segment['end'])
                text = segment['text'].strip()
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _generate_ass_lyrics(self, song: Dict, srt_path: str) -> Optional[str]:
        """Generate ASS karaoke file from SRT"""
        try:
            logger.info("Generating ASS karaoke lyrics")
            
            output_dir = Path(self.paths['processed']) / song['youtube_id']
            ass_path = output_dir / 'lyrics.ass'
            
            result_path = self.lyrics_generator.srt_to_ass_karaoke(
                str(srt_path),
                str(ass_path)
            )
            
            # Validate
            if not self.lyrics_generator.validate_ass_file(result_path):
                raise ValueError("Invalid ASS file generated")
            
            # Update database
            self.db.update_paths(
                song['youtube_id'],
                lyrics_path=result_path
            )
            
            return result_path
        
        except Exception as e:
            logger.error(f"Error generating ASS lyrics: {e}")
            return None
    
    def _generate_video(self, song: Dict, audio_path: str, lyrics_path: str) -> Optional[str]:
        """Generate karaoke video"""
        try:
            self.db.update_status(song['youtube_id'], SongStatus.GENERATING_VIDEO)
            logger.info("Generating karaoke video")
            
            safe_title = sanitize_filename(f"{song['artist']} - {song['title']}")
            output_path = Path(self.paths['videos']) / f"{safe_title}_{song['youtube_id']}.mp4"
            
            result_path = self.video_generator.create_karaoke_video(
                audio_path=audio_path,
                lyrics_ass_path=lyrics_path,
                output_path=str(output_path)
            )
            
            # Verify video
            verification = self.video_generator.verify_video(result_path)
            if not verification.get('valid'):
                raise ValueError("Video verification failed")
            
            logger.info(f"Video generated: {get_file_size_mb(result_path):.1f} MB, "
                       f"{verification.get('duration', 0):.1f}s")
            
            # Update database
            self.db.update_paths(
                song['youtube_id'],
                video_path=result_path
            )
            
            return result_path
        
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            return None
    
    def _upload_to_youtube(self, song: Dict, video_path: str) -> Optional[str]:
        """Upload video to YouTube"""
        try:
            if not self.youtube_uploader.check_upload_enabled():
                logger.info("⏭️  YouTube upload DISABLED in config - Skipping upload")
                logger.info(f"📹 Video saved locally at: {video_path}")
                return None
            
            self.db.update_status(song['youtube_id'], SongStatus.UPLOADING)
            logger.info("Uploading to YouTube")
            
            youtube_video_id = self.youtube_uploader.upload_karaoke_video(
                video_path=video_path,
                song_info=song
            )
            
            if youtube_video_id:
                # Update database
                self.db.update_paths(
                    song['youtube_id'],
                    youtube_upload_id=youtube_video_id
                )
                return youtube_video_id
            
            return None
        
        except Exception as e:
            logger.error(f"Error uploading to YouTube: {e}")
            return None


if __name__ == "__main__":
    # Test processor
    from utils import load_config, setup_logging
    
    config = load_config()
    setup_logging(config)
    
    db = Database(config['paths']['database'])
    processor = KaraokeProcessor(config, db)
    
    print("Processor module loaded successfully")
    print(f"Whisper model: {config['audio']['transcription']['model']}")
    print(f"Separation model: {processor.separation_model}")
