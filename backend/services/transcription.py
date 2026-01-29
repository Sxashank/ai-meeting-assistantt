import whisper
import torch
import logging
from typing import Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self):
        self.model_name = "base"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading Whisper model '{self.model_name}' on {self.device}")
        self.model = whisper.load_model(self.model_name, device=self.device)
        logger.info("Whisper model loaded successfully")
    
    async def transcribe(self, audio_data: np.ndarray) -> Dict[str, Any]:
        try:
            logger.info("Starting transcription...")
            result = self.model.transcribe(
                audio_data,
                fp16=False,
                verbose=True,
                task="transcribe",
                language=None
            )
            logger.info(f"Transcription complete. Language: {result['language']}")
            return {
                "text": result["text"],
                "segments": [
                    {
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": seg["text"].strip()
                    }
                    for seg in result["segments"]
                ],
                "language": result["language"]
            }
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise