"""
Video Generator - Create karaoke videos using FFmpeg
Combines audio, lyrics (ASS), background, and audio visualizer
"""

import subprocess
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
import random


class VideoGenerator:
    def __init__(self, config: Dict):
        self.config = config
        self.video_config = config['video']
        self.paths = config['paths']
        
        # Video settings
        self.resolution = self.video_config['resolution']
        self.fps = self.video_config['fps']
        self.width, self.height = map(int, self.resolution.split('x'))
    
    def create_karaoke_video(
        self,
        audio_path: str,
        lyrics_ass_path: str,
        output_path: str,
        background_path: Optional[str] = None
    ) -> str:
        """
        Create complete karaoke video with all effects
        
        Args:
            audio_path: Path to instrumental audio (modified)
            lyrics_ass_path: Path to ASS subtitle file
            output_path: Path for output video
            background_path: Optional custom background image/video
        
        Returns:
            Path to created video file
        """
        try:
            logger.info(f"Creating karaoke video: {Path(output_path).name}")
            
            # Select or create background
            if not background_path:
                background_path = self._get_background()
            
            # Build FFmpeg command
            ffmpeg_cmd = self._build_ffmpeg_command(
                audio_path=audio_path,
                background_path=background_path,
                lyrics_ass_path=lyrics_ass_path,
                output_path=output_path
            )
            
            logger.debug(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")
            
            # Execute FFmpeg
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise RuntimeError(f"FFmpeg failed with code {result.returncode}")
            
            if not Path(output_path).exists():
                raise FileNotFoundError(f"Output video not created: {output_path}")
            
            # Get file size
            file_size_mb = Path(output_path).stat().st_size / (1024 * 1024)
            logger.info(f"Video created successfully: {Path(output_path).name} ({file_size_mb:.2f} MB)")
            
            return output_path
        
        except Exception as e:
            logger.error(f"Error creating karaoke video: {e}")
            raise
    
    def _build_ffmpeg_command(
        self,
        audio_path: str,
        background_path: str,
        lyrics_ass_path: str,
        output_path: str
    ) -> list:
        """
        Build FFmpeg command with all filters and effects
        
        Filter chain:
        1. Background (image/video/gradient)
        2. Audio visualizer (waveform/spectrum)
        3. Lyrics overlay (ASS subtitles)
        """
        
        # Check if background is image or video
        bg_ext = Path(background_path).suffix.lower()
        is_video_bg = bg_ext in ['.mp4', '.mov', '.avi', '.mkv']
        
        # Get audio duration for loop length
        duration_cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ]
        
        try:
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
            duration = float(duration_result.stdout.strip())
        except:
            duration = 180  # Fallback to 3 minutes
        
        # Build filter complex for video generation
        visualizer_config = self.video_config.get('visualizer', {})
        vis_type = visualizer_config.get('type', 'waveform')
        vis_color = visualizer_config.get('color', 'cyan')
        vis_height = visualizer_config.get('height', 200)
        vis_position = visualizer_config.get('position', 'bottom')
        
        # Calculate visualizer position
        if vis_position == 'bottom':
            vis_y = self.height - vis_height - 20
        elif vis_position == 'top':
            vis_y = 20
        else:  # center
            vis_y = (self.height - vis_height) // 2
        
        # Background input handling
        if is_video_bg:
            bg_input = ['-stream_loop', '-1', '-i', background_path]
            bg_filter = f"[1:v]scale={self.width}:{self.height}:force_original_aspect_ratio=increase,crop={self.width}:{self.height}[bg]"
        else:
            bg_input = ['-loop', '1', '-i', background_path]
            bg_filter = f"[1:v]scale={self.width}:{self.height}[bg]"
        
        # Visualizer filter
        if vis_type == 'waveform':
            vis_filter = (
                f"[0:a]showwaves=s={self.width}x{vis_height}:mode=cline:"
                f"colors={vis_color}:scale=sqrt[waves];"
            )
        else:  # spectrum
            vis_filter = (
                f"[0:a]showfreqs=s={self.width}x{vis_height}:mode=bar:"
                f"colors={vis_color}[waves];"
            )
        
        # Overlay visualizer on background
        overlay_filter = (
            f"[bg][waves]overlay=0:{vis_y}[video_with_waves];"
        )
        
        # Complete filter complex
        filter_complex = bg_filter + ";" + vis_filter + overlay_filter + (
            f"[video_with_waves]ass='{lyrics_ass_path}'[out]"
        )
        
        # Build complete FFmpeg command
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-i', audio_path,  # Input 0: audio
        ] + bg_input + [  # Input 1: background
            '-filter_complex', filter_complex,
            '-map', '[out]',  # Map filtered video
            '-map', '0:a',  # Map audio
            '-c:v', 'libx264',  # H.264 codec
            '-preset', 'medium',  # Encoding preset
            '-crf', '23',  # Quality (lower = better, 18-28 typical)
            '-c:a', 'aac',  # AAC audio codec
            '-b:a', '192k',  # Audio bitrate
            '-ar', '44100',  # Sample rate
            '-t', str(duration),  # Duration
            '-r', str(self.fps),  # Frame rate
            '-pix_fmt', 'yuv420p',  # Pixel format (widely compatible)
            output_path
        ]
        
        return cmd
    
    def _get_background(self) -> str:
        """
        Get background image/video for karaoke
        Generates gradient or uses existing background
        """
        bg_type = self.video_config.get('background_type', 'gradient')
        backgrounds_dir = Path(self.paths['backgrounds'])
        
        if bg_type == 'gradient':
            # Generate gradient background
            gradient_path = backgrounds_dir / 'gradient_bg.png'
            if not gradient_path.exists():
                self._create_gradient_background(str(gradient_path))
            return str(gradient_path)
        
        # Look for existing backgrounds
        background_files = list(backgrounds_dir.glob('*'))
        background_files = [
            f for f in background_files 
            if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.mp4', '.mov']
        ]
        
        if background_files:
            # Select random background
            return str(random.choice(background_files))
        
        # Fallback: create gradient
        gradient_path = backgrounds_dir / 'gradient_bg.png'
        self._create_gradient_background(str(gradient_path))
        return str(gradient_path)
    
    def _create_gradient_background(self, output_path: str):
        """Create a gradient background image using FFmpeg"""
        try:
            logger.info("Creating gradient background")
            
            # Create attractive gradient with FFmpeg
            # Using lavfi (Libavfilter virtual input device)
            cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', f'color=c=#1a1a2e:s={self.width}x{self.height}:d=1',
                '-f', 'lavfi',
                '-i', f'color=c=#16213e:s={self.width}x{self.height}:d=1',
                '-filter_complex',
                '[0:v][1:v]blend=all_mode=average:all_opacity=0.5',
                '-frames:v', '1',
                output_path
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            logger.info(f"Gradient background created: {output_path}")
        
        except Exception as e:
            logger.error(f"Error creating gradient background: {e}")
            # Create solid color as fallback
            self._create_solid_background(output_path, color='#1a1a2e')
    
    def _create_solid_background(self, output_path: str, color: str = '#000000'):
        """Create a solid color background"""
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'color=c={color}:s={self.width}x{self.height}:d=1',
            '-frames:v', '1',
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
    
    def verify_video(self, video_path: str) -> Dict:
        """
        Verify video file and get properties
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,duration,bit_rate',
                '-of', 'json',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse JSON output
            import json
            data = json.loads(result.stdout)
            
            if data.get('streams'):
                stream = data['streams'][0]
                return {
                    'width': stream.get('width'),
                    'height': stream.get('height'),
                    'duration': float(stream.get('duration', 0)),
                    'bit_rate': int(stream.get('bit_rate', 0)),
                    'valid': True
                }
        
        except Exception as e:
            logger.error(f"Error verifying video: {e}")
        
        return {'valid': False}


if __name__ == "__main__":
    # Test the video generator
    from utils import load_config, setup_logging
    
    config = load_config()
    setup_logging(config)
    
    generator = VideoGenerator(config)
    
    print("Video generator module loaded successfully")
    print(f"Resolution: {generator.resolution}")
    print(f"FPS: {generator.fps}")
