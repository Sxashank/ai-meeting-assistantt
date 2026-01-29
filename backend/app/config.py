from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Meeting Assistant"

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000"
    ]

    WHISPER_MODEL: str = "base"
    WHISPER_DEVICE: str = "cpu"
    USE_ONNX: bool = True

    DIARIZATION_MODEL: str = "pyannote/speaker-diarization-3.1"
    HF_TOKEN: str | None = None  # Loaded from .env file

    SUMMARIZATION_MODEL: str = "facebook/bart-large-cnn"

    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024
    ALLOWED_AUDIO_FORMATS: List[str] = [".wav", ".mp3", ".m4a", ".flac", ".ogg"]

    UPLOAD_DIR: str = "uploads"
    MODEL_CACHE_DIR: str = "models"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
