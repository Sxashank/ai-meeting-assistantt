import librosa
import numpy as np
import soundfile as sf
from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.target_sr = 16000
        logger.info("AudioProcessor initialized")
    
    def load_audio(self, file_path: str, sr: Optional[int] = None, mono: bool = True) -> np.ndarray:
        try:
            if sr is None:
                sr = self.target_sr
            logger.info(f"Loading audio: {file_path}")
            audio, original_sr = librosa.load(file_path, sr=sr, mono=mono, duration=None)
            logger.info(f"Loaded audio: {len(audio)} samples at {sr}Hz")
            logger.info(f"Duration: {len(audio) / sr:.2f} seconds")
            audio = self.normalize_audio(audio)
            return audio
        except Exception as e:
            logger.error(f"Error loading audio: {str(e)}")
            raise
    
    def normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        max_val = np.abs(audio).max()
        if max_val > 0:
            audio = audio / max_val
        return audio
    
    def trim_silence(self, audio: np.ndarray, top_db: int = 20) -> np.ndarray:
        intervals = librosa.effects.split(audio, top_db=top_db)
        if len(intervals) == 0:
            logger.warning("No non-silent segments found")
            return audio
        trimmed = np.concatenate([audio[start:end] for start, end in intervals])
        removed_duration = (len(audio) - len(trimmed)) / self.target_sr
        logger.info(f"Trimmed {removed_duration:.2f} seconds of silence")
        return trimmed
    
    def get_duration(self, audio: np.ndarray, sr: Optional[int] = None) -> float:
        if sr is None:
            sr = self.target_sr
        duration = len(audio) / sr
        return round(duration, 2)
    
    def save_audio(self, audio: np.ndarray, output_path: str, sr: Optional[int] = None):
        if sr is None:
            sr = self.target_sr
        logger.info(f"Saving audio to: {output_path}")
        sf.write(output_path, audio, sr)
        logger.info("Audio saved successfully")