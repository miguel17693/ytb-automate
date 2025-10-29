"""
Lyrics Generator - Convert SRT subtitles to ASS format with karaoke styling
Creates visually appealing lyrics with word-by-word highlighting
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple
from loguru import logger


class LyricsGenerator:
    def __init__(self, config: Dict):
        self.config = config
        self.lyrics_config = config['video']['lyrics']
        self.video_config = config['video']
    
    def srt_to_ass_karaoke(self, srt_path: str, output_path: str) -> str:
        """
        Convert SRT subtitle file to ASS format with karaoke effects
        
        Args:
            srt_path: Path to input SRT file from Whisper
            output_path: Path to output ASS file
        
        Returns:
            Path to created ASS file
        """
        try:
            logger.info(f"Converting SRT to ASS karaoke: {Path(srt_path).name}")
            
            # Parse SRT file
            subtitles = self._parse_srt(srt_path)
            
            if not subtitles:
                raise ValueError("No subtitles found in SRT file")
            
            # Generate ASS content
            ass_content = self._generate_ass_content(subtitles)
            
            # Write to file
            output_path = str(output_path)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)
            
            logger.info(f"ASS karaoke file created: {Path(output_path).name}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error converting SRT to ASS: {e}")
            raise
    
    def _parse_srt(self, srt_path: str) -> List[Dict]:
        """Parse SRT file into list of subtitle dictionaries"""
        subtitles = []
        
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by double newline (subtitle blocks)
        blocks = re.split(r'\n\n+', content.strip())
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            # Parse timing line (format: 00:00:01,000 --> 00:00:03,500)
            timing_match = re.match(
                r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})',
                lines[1]
            )
            
            if not timing_match:
                continue
            
            start_h, start_m, start_s, start_ms, end_h, end_m, end_s, end_ms = timing_match.groups()
            
            start_time = self._time_to_seconds(int(start_h), int(start_m), int(start_s), int(start_ms))
            end_time = self._time_to_seconds(int(end_h), int(end_m), int(end_s), int(end_ms))
            
            # Get text (can be multiple lines)
            text = ' '.join(lines[2:])
            
            subtitles.append({
                'start': start_time,
                'end': end_time,
                'text': text
            })
        
        logger.debug(f"Parsed {len(subtitles)} subtitles from SRT")
        return subtitles
    
    def _time_to_seconds(self, hours: int, minutes: int, seconds: int, milliseconds: int) -> float:
        """Convert time components to total seconds"""
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
    
    def _seconds_to_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format (H:MM:SS.CC)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)
        
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"
    
    def _generate_ass_content(self, subtitles: List[Dict]) -> str:
        """Generate complete ASS file content with styling"""
        
        resolution = self.video_config['resolution']
        width, height = map(int, resolution.split('x'))
        
        # ASS header
        ass_content = f"""[Script Info]
Title: Karaoke Lyrics
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Karaoke,{self.lyrics_config['font']},{self.lyrics_config['font_size']},{self.lyrics_config['primary_color']},{self.lyrics_config['highlight_color']},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{self.lyrics_config['border_size']},{self.lyrics_config['shadow_depth']},2,50,50,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        # Add subtitle events with karaoke effects
        for sub in subtitles:
            start_time = self._seconds_to_ass_time(sub['start'])
            end_time = self._seconds_to_ass_time(sub['end'])
            text = sub['text']
            
            # Apply karaoke effect with word-by-word highlighting
            karaoke_text = self._apply_karaoke_effect(text, sub['start'], sub['end'])
            
            ass_content += f"Dialogue: 0,{start_time},{end_time},Karaoke,,0,0,0,,{karaoke_text}\n"
        
        return ass_content
    
    def _apply_karaoke_effect(self, text: str, start_time: float, end_time: float) -> str:
        """
        Apply karaoke effect tags to text for word-by-word highlighting
        
        ASS karaoke tags:
        - \\k<duration> - Karaoke effect that highlights for <duration> centiseconds
        - \\fad(in,out) - Fade in/out effect
        """
        words = text.split()
        if not words:
            return text
        
        # Calculate duration per word
        total_duration = end_time - start_time
        duration_per_word = total_duration / len(words)
        duration_centiseconds = int(duration_per_word * 100)
        
        # Build karaoke text with tags
        fade_in = self.lyrics_config.get('fade_in_ms', 200)
        fade_out = self.lyrics_config.get('fade_out_ms', 200)
        
        # Add fade effect
        karaoke_text = f"{{\\fad({fade_in},{fade_out})}}"
        
        # Add word-by-word karaoke timing
        for word in words:
            # \\k tag makes the word highlight for the specified duration
            karaoke_text += f"{{\\k{duration_centiseconds}}}{word} "
        
        return karaoke_text.strip()
    
    def create_simple_ass(self, text_lines: List[str], output_path: str, 
                         duration_per_line: float = 3.0) -> str:
        """
        Create a simple ASS file from plain text lines
        Useful for manual lyrics or when Whisper fails
        
        Args:
            text_lines: List of lyrics lines
            output_path: Output ASS file path
            duration_per_line: Seconds to display each line
        """
        subtitles = []
        current_time = 0
        
        for line in text_lines:
            if line.strip():
                subtitles.append({
                    'start': current_time,
                    'end': current_time + duration_per_line,
                    'text': line.strip()
                })
                current_time += duration_per_line
        
        ass_content = self._generate_ass_content(subtitles)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        logger.info(f"Created simple ASS file: {Path(output_path).name}")
        return output_path
    
    def validate_ass_file(self, ass_path: str) -> bool:
        """Validate that ASS file is properly formatted"""
        try:
            with open(ass_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for required sections
            required_sections = ['[Script Info]', '[V4+ Styles]', '[Events]']
            for section in required_sections:
                if section not in content:
                    logger.error(f"Missing required section: {section}")
                    return False
            
            # Check for at least one dialogue line
            if 'Dialogue:' not in content:
                logger.error("No dialogue lines found in ASS file")
                return False
            
            logger.info("ASS file validation passed")
            return True
        
        except Exception as e:
            logger.error(f"Error validating ASS file: {e}")
            return False


if __name__ == "__main__":
    # Test the lyrics generator
    from utils import load_config, setup_logging
    
    config = load_config()
    setup_logging(config)
    
    generator = LyricsGenerator(config)
    
    # Test with sample SRT (you'd need to provide one)
    # srt_file = "test_lyrics.srt"
    # ass_file = "test_karaoke.ass"
    # 
    # if Path(srt_file).exists():
    #     result = generator.srt_to_ass_karaoke(srt_file, ass_file)
    #     print(f"Created: {result}")
    #     
    #     # Validate
    #     is_valid = generator.validate_ass_file(result)
    #     print(f"Valid: {is_valid}")
    # else:
    #     print(f"Test file not found: {srt_file}")
    
    print("Lyrics generator module loaded successfully")
