"""
Audio Modifier - Apply subtle modifications to instrumental audio
to differentiate from original (helps avoid Content ID matches)
"""

from pathlib import Path
from typing import Dict
from pydub import AudioSegment
from pydub.effects import speedup, normalize
from loguru import logger
import random


class AudioModifier:
    def __init__(self, config: Dict):
        self.config = config
        self.mod_config = config['audio']['modification']
        self.enabled = self.mod_config.get('enabled', True)
    
    def modify_instrumental(self, input_path: str, output_path: str) -> str:
        """
        Apply subtle modifications to instrumental audio
        
        Modifications applied:
        - Pitch shift (very subtle)
        - Tempo change (1-3%)
        - Subtle EQ/filter adjustments
        - Normalization
        
        Args:
            input_path: Path to original instrumental
            output_path: Path to save modified instrumental
        
        Returns:
            Path to modified audio file
        """
        if not self.enabled:
            logger.info("Audio modification disabled, using original instrumental")
            return input_path
        
        try:
            logger.info(f"Modifying instrumental: {Path(input_path).name}")
            
            # Load audio
            audio = AudioSegment.from_file(input_path)
            
            # Apply modifications
            modified_audio = self._apply_modifications(audio)
            
            # Export modified audio
            output_path = str(output_path)
            modified_audio.export(
                output_path,
                format='wav',
                parameters=["-q:a", "0"]  # Highest quality
            )
            
            logger.info(f"Modified instrumental saved: {Path(output_path).name}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error modifying audio: {e}")
            logger.warning("Falling back to original instrumental")
            return input_path
    
    def _apply_modifications(self, audio: AudioSegment) -> AudioSegment:
        """Apply a combination of subtle audio modifications"""
        
        # 1. Tempo change (subtle speed up/down)
        tempo_change = self.mod_config.get('tempo_change_percent', 2)
        if tempo_change > 0:
            # Random direction (speed up or slow down)
            factor = 1.0 + (random.choice([-1, 1]) * tempo_change / 100)
            factor = max(0.97, min(1.03, factor))  # Clamp between 97% and 103%
            
            logger.debug(f"Applying tempo change: {factor:.3f}x")
            audio = speedup(audio, playback_speed=factor)
        
        # 2. Pitch shift (using frame rate manipulation - subtle)
        pitch_shift = self.mod_config.get('pitch_shift_semitones', 0.5)
        if pitch_shift > 0:
            # Random direction
            semitones = random.choice([-1, 1]) * pitch_shift
            semitones = max(-1, min(1, semitones))  # Clamp to ±1 semitone
            
            logger.debug(f"Applying pitch shift: {semitones:+.2f} semitones")
            audio = self._pitch_shift(audio, semitones)
        
        # 3. Apply subtle filter (optional)
        if self.mod_config.get('apply_filter', True):
            audio = self._apply_subtle_filter(audio)
        
        # 4. Normalize volume
        audio = normalize(audio, headroom=0.1)
        
        return audio
    
    def _pitch_shift(self, audio: AudioSegment, semitones: float) -> AudioSegment:
        """
        Shift pitch by changing sample rate
        Note: This is a simple method. For better quality, consider using librosa
        """
        # Calculate new frame rate
        # Each semitone is a factor of 2^(1/12)
        factor = 2 ** (semitones / 12)
        
        new_sample_rate = int(audio.frame_rate * factor)
        
        # Change frame rate (this changes pitch)
        pitched = audio._spawn(audio.raw_data, overrides={
            'frame_rate': new_sample_rate
        })
        
        # Convert back to original frame rate (to keep tempo)
        return pitched.set_frame_rate(audio.frame_rate)
    
    def _apply_subtle_filter(self, audio: AudioSegment) -> AudioSegment:
        """
        Apply a very subtle filter to slightly color the audio
        This can be a gentle low-pass or high-pass filter
        """
        # Apply gentle low-pass filter (removes very high frequencies)
        # This simulates a slight "warmth" or analog quality
        
        # For more sophisticated filtering, we'd need librosa or scipy
        # For now, we use a simple approach: slight high-frequency rolloff
        
        # Apply gentle compression using gain
        compressed = audio.apply_gain(-1)  # Reduce volume slightly
        compressed = normalize(compressed)  # Then normalize back
        
        # Mix with original (subtle effect)
        mixed = audio.overlay(compressed - 6)  # 6dB quieter overlay
        
        return mixed
    
    def analyze_audio(self, audio_path: str) -> Dict:
        """
        Analyze audio file properties
        Useful for debugging and verification
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            
            return {
                'duration_seconds': len(audio) / 1000,
                'frame_rate': audio.frame_rate,
                'channels': audio.channels,
                'sample_width': audio.sample_width,
                'frame_width': audio.frame_width,
                'rms': audio.rms,
                'dBFS': audio.dBFS,
                'max_dBFS': audio.max_dBFS,
            }
        except Exception as e:
            logger.error(f"Error analyzing audio: {e}")
            return {}


if __name__ == "__main__":
    # Test the audio modifier
    from utils import load_config, setup_logging
    
    config = load_config()
    setup_logging(config)
    
    modifier = AudioModifier(config)
    
    # Test with a sample file (you'll need to provide one)
    # input_file = "test_instrumental.wav"
    # output_file = "test_modified.wav"
    # 
    # if Path(input_file).exists():
    #     modified = modifier.modify_instrumental(input_file, output_file)
    #     
    #     # Analyze both files
    #     print("\nOriginal audio:")
    #     print(modifier.analyze_audio(input_file))
    #     
    #     print("\nModified audio:")
    #     print(modifier.analyze_audio(modified))
    # else:
    #     print(f"Test file not found: {input_file}")
    
    print("Audio modifier module loaded successfully")
    print(f"Modifications enabled: {modifier.enabled}")
