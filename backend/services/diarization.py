import logging
import torch
from typing import List, Dict, Optional
from pathlib import Path
import threading
from app.config import settings

logger = logging.getLogger(__name__)


class DiarizationService:
    """
    Singleton pattern for pyannote speaker diarization.
    Lazy-loads model on first use to avoid blocking FastAPI startup.
    Includes GPU/CPU handling, error handling, and comprehensive logging.
    """

    _instance: Optional['DiarizationService'] = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DiarizationService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not DiarizationService._initialized:
            with DiarizationService._lock:
                if not DiarizationService._initialized:
                    self.pipeline = None
                    self.device = self._get_device()
                    self._is_loading = False
                    DiarizationService._initialized = True
                    logger.info(f"DiarizationService initialized (lazy-load mode, device: {self.device})")

    def _get_device(self) -> str:
        """Determine optimal device for model inference."""
        if torch.cuda.is_available():
            device = "cuda"
            logger.info(f"GPU available: {torch.cuda.get_device_name(0)}")
        else:
            device = "cpu"
            logger.info("GPU not available, using CPU for diarization")
        return device

    def _load_pipeline(self) -> bool:
        """
        Lazy-load the diarization pipeline on first use.
        Returns True if successful, False otherwise.
        """
        if self.pipeline is not None:
            return True

        if self._is_loading:
            logger.warning("Diarization pipeline is already loading, skipping duplicate load")
            return False

        if not settings.HF_TOKEN:
            logger.error(
                "HF_TOKEN not configured. Set HF_TOKEN in .env file to enable speaker diarization. "
                "Get token from: https://huggingface.co/settings/tokens"
            )
            return False

        try:
            self._is_loading = True
            logger.info(f"Loading {settings.DIARIZATION_MODEL} (this may take a moment)...")

            from pyannote.audio import Pipeline

            self.pipeline = Pipeline.from_pretrained(
                settings.DIARIZATION_MODEL,
                use_auth_token=settings.HF_TOKEN
            )

            # Move to appropriate device
            self.pipeline.to(torch.device(self.device))
            logger.info(f"Diarization pipeline loaded successfully on {self.device}")
            return True

        except Exception as e:
            logger.error(f"Failed to load diarization pipeline: {str(e)}", exc_info=True)
            return False
        finally:
            self._is_loading = False

    async def diarize(self, audio_path: str) -> List[Dict]:
        """
        Perform speaker diarization on audio file.
        Returns list of diarization segments with speaker labels.
        Gracefully handles failures to ensure backend stability.
        """
        if not Path(audio_path).exists():
            logger.error(f"Audio file not found: {audio_path}")
            return []

        try:
            # Lazy-load pipeline
            if not self._load_pipeline():
                logger.warning("Diarization skipped due to pipeline load failure. Returning empty diarization.")
                return []

            if self.pipeline is None:
                logger.warning("Diarization pipeline is None. Returning empty diarization.")
                return []

            logger.info(f"Starting speaker diarization for: {audio_path}")

            # Run diarization
            diarization = self.pipeline(audio_path)

            # Convert pyannote output to our format
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segment = {
                    "start": float(turn.start),
                    "end": float(turn.end),
                    "speaker": speaker,
                    "duration": float(turn.end - turn.start)
                }
                segments.append(segment)

            logger.info(f"Diarization completed: {len(segments)} speaker segments detected")
            return segments

        except Exception as e:
            logger.error(
                f"Diarization processing failed: {str(e)}",
                exc_info=True
            )
            logger.warning("Continuing without diarization. Transcription, summary, and action items will be processed normally.")
            return []

    def get_status(self) -> Dict:
        """Get diarization service status for debugging."""
        return {
            "available": self.pipeline is not None,
            "device": self.device,
            "hf_token_configured": bool(settings.HF_TOKEN),
            "model": settings.DIARIZATION_MODEL
        }
