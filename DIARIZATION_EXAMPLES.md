# Diarization Code Examples & Best Practices

## Core Implementation Reference

### Singleton Pattern Used

```python
class DiarizationService:
    _instance: Optional['DiarizationService'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not DiarizationService._initialized:
            # Initialize only once
            self.pipeline = None
            self.device = self._get_device()
            DiarizationService._initialized = True
```

**Why Singleton?**
- ✅ Ensures only one model instance in memory
- ✅ Thread-safe (uses lock)
- ✅ Lazy loaded (doesn't block startup)
- ✅ Reused across multiple requests

## Device Detection

```python
def _get_device(self) -> str:
    """Automatically select GPU or CPU"""
    if torch.cuda.is_available():
        device = "cuda"
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
    else:
        device = "cpu"
        logger.info("Using CPU")
    return device
```

**Usage**:
```python
# Model automatically moves to correct device
self.pipeline.to(torch.device(self.device))
```

## Error-Safe Diarization

```python
async def diarize(self, audio_path: str) -> List[Dict]:
    """Diarization that never crashes the backend"""
    
    # Validate input
    if not Path(audio_path).exists():
        logger.error(f"Audio file not found: {audio_path}")
        return []  # Return empty, not exception

    try:
        # Lazy-load pipeline if needed
        if not self._load_pipeline():
            return []  # Pipeline load failed

        if self.pipeline is None:
            return []  # Pipeline is None

        logger.info(f"Diarizing: {audio_path}")

        # Perform diarization
        diarization = self.pipeline(audio_path)

        # Convert to our format
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "start": float(turn.start),
                "end": float(turn.end),
                "speaker": speaker,
                "duration": float(turn.end - turn.start)
            })

        logger.info(f"Diarization success: {len(segments)} segments")
        return segments

    except Exception as e:
        logger.error(f"Diarization failed: {str(e)}", exc_info=True)
        logger.warning("Returning empty diarization; backend continues normally")
        return []
```

**Key Points**:
- Returns `[]` (empty list) on any failure
- Never raises exceptions
- Detailed logging for debugging
- Backend continues processing

## Lazy Loading Pattern

```python
def _load_pipeline(self) -> bool:
    """Load model only when first needed"""
    
    # Already loaded?
    if self.pipeline is not None:
        return True

    # Already loading? (prevent duplicate loads)
    if self._is_loading:
        logger.warning("Already loading, skipping duplicate")
        return False

    # Check prerequisites
    if not settings.YOUR_HF_TOKEN:
        logger.error("YOUR_HF_TOKEN not configured")
        return False

    try:
        self._is_loading = True
        logger.info(f"Loading {settings.DIARIZATION_MODEL}...")

        from pyannote.audio import Pipeline

        # Load from HuggingFace
        self.pipeline = Pipeline.from_pretrained(
            settings.DIARIZATION_MODEL,
            use_auth_token=settings.YOUR_HF_TOKEN
        )

        # Move to device
        self.pipeline.to(torch.device(self.device))
        logger.info(f"Pipeline loaded on {self.device}")
        return True

    except Exception as e:
        logger.error(f"Load failed: {str(e)}", exc_info=True)
        return False
    finally:
        self._is_loading = False
```

**Benefits**:
- ✅ FastAPI starts immediately (no model download)
- ✅ Model downloaded on first request
- ✅ Prevents duplicate loading
- ✅ Clear error messages

## API Integration

```python
@router.post("/meetings/upload", response_model=MeetingResponse)
async def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process meeting audio"""
    try:
        # Validate, save, load audio...
        
        # Transcription (required)
        logger.info("Transcribing...")
        transcription = await transcription_service.transcribe(audio_data)

        # Diarization (optional, safe to fail)
        logger.info("Diarizing...")
        diarization = await diarization_service.diarize(file_path)
        
        if diarization:
            logger.info(f"{len(diarization)} speakers detected")
        else:
            logger.warning("Diarization failed or returned empty")

        # Merge results
        transcript_with_speakers = merge_transcription_diarization(
            transcription, diarization
        )

        # Summary & Action Items (required)
        summary = await summarization_service.summarize(...)
        action_items = await action_item_extractor.extract(...)

        # Return complete response (works even if diarization failed)
        return {
            "meeting_id": meeting_id,
            "transcription": transcript_with_speakers,
            "summary": summary,
            "action_items": action_items,
            ...
        }

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

## Merging Diarization with Transcription

```python
def merge_transcription_diarization(transcription, diarization):
    """Assign speakers to transcription segments"""
    
    segments_with_speakers = []

    if diarization:
        # Map diarization speakers to transcription segments
        for segment in transcription["segments"]:
            segment_start = segment["start"]
            segment_end = segment["end"]

            # Find overlapping diarization segment
            speaker = "Speaker_0"  # Default fallback
            for dia in diarization:
                if (dia["start"] < segment_end and
                    dia["end"] > segment_start):
                    speaker = dia["speaker"]
                    break

            segments_with_speakers.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"],
                "speaker": speaker
            })
    else:
        # No diarization: use generic speaker labels
        logger.debug("No diarization, using generic labels")
        for segment in transcription["segments"]:
            segments_with_speakers.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"],
                "speaker": "Speaker_0"
            })

    return {
        "full_text": transcription["text"],
        "segments": segments_with_speakers,
        "language": transcription.get("language", "en")
    }
```

## Configuration Best Practices

### .env File
```env
# NEVER commit this file to git!
# Add to .gitignore:

# Required for diarization
YOUR_HF_TOKEN=YOUR_HF_TOKEN

# Optional configurations
DIARIZATION_MODEL=pyannote/speaker-diarization-3.1
WHISPER_DEVICE=cuda  # Use GPU if available
```

### Loading Config
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    YOUR_HF_TOKEN: str | None = None  # Auto-loaded from .env
    DIARIZATION_MODEL: str = "pyannote/speaker-diarization-3.1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### In Main App
```python
from app.config import settings

# Ensure config is loaded
if not settings.YOUR_HF_TOKEN:
    logger.warning("YOUR_HF_TOKEN not configured in .env")
else:
    logger.info("YOUR_HF_TOKEN loaded from .env")
```

## Logging Best Practices

```python
import logging

logger = logging.getLogger(__name__)

# INFO: Normal operation
logger.info("Pipeline loaded successfully")

# WARNING: Issues but continuing
logger.warning("Diarization returned empty, using fallback")

# ERROR: Failure with full details
logger.error(
    f"Diarization failed: {error_message}",
    exc_info=True  # Include full traceback
)
```

### Enable Debug Logging
```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Or for specific module:
logging.getLogger("services.diarization").setLevel(logging.DEBUG)
```

## Testing Examples

### Unit Test
```python
import pytest
from services.diarization import DiarizationService

@pytest.mark.asyncio
async def test_diarization_no_YOUR_HF_TOKEN(monkeypatch):
    """Test graceful failure without HF token"""
    monkeypatch.setattr("app.config.settings.YOUR_HF_TOKEN", None)
    
    service = DiarizationService()
    result = await service.diarize("test.wav")
    
    assert result == []  # Returns empty, doesn't crash

@pytest.mark.asyncio
async def test_diarization_missing_file():
    """Test graceful failure with missing file"""
    service = DiarizationService()
    result = await service.diarize("nonexistent.wav")
    
    assert result == []  # Returns empty, doesn't crash
```

### Integration Test
```python
import asyncio
from services.diarization import DiarizationService

async def test_real_diarization():
    """Test with real audio file"""
    service = DiarizationService()
    
    # First call: loads model
    result1 = await service.diarize("meeting.wav")
    assert isinstance(result1, list)
    
    # Second call: uses cached model
    result2 = await service.diarize("another_meeting.wav")
    assert isinstance(result2, list)
    
    # Verify service status
    status = service.get_status()
    assert status["available"] == True
    assert status["device"] in ["cpu", "cuda"]

asyncio.run(test_real_diarization())
```

## Performance Optimization

### Caching Pattern (Future Enhancement)
```python
from functools import lru_cache
import hashlib

class DiarizationCache:
    """Cache diarization results for identical audio"""
    
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
    
    def get_cache_key(self, audio_path):
        """Create hash of audio file"""
        with open(audio_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    async def get_diarization(self, audio_path, service):
        """Get cached or compute diarization"""
        key = self.get_cache_key(audio_path)
        
        if key in self.cache:
            logger.info("Using cached diarization")
            return self.cache[key]
        
        result = await service.diarize(audio_path)
        
        if len(self.cache) >= self.max_size:
            self.cache.pop(next(iter(self.cache)))  # Remove oldest
        
        self.cache[key] = result
        return result
```

### Batch Processing (Future Enhancement)
```python
async def diarize_batch(
    service: DiarizationService,
    audio_paths: List[str]
) -> List[List[Dict]]:
    """Process multiple audio files efficiently"""
    tasks = [service.diarize(path) for path in audio_paths]
    return await asyncio.gather(*tasks)

# Usage:
files = ["meeting1.wav", "meeting2.wav", "meeting3.wav"]
results = await diarize_batch(service, files)
```

## Error Recovery

```python
async def diarize_with_retry(
    service: DiarizationService,
    audio_path: str,
    max_retries: int = 2
) -> List[Dict]:
    """Diarize with retry logic"""
    
    for attempt in range(max_retries):
        try:
            result = await service.diarize(audio_path)
            if result:
                return result
            
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} returned empty, retrying...")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.warning("Diarization failed after retries, returning empty")
                return []
        
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
                await asyncio.sleep(2 ** attempt)
            else:
                logger.error(f"Diarization failed after {max_retries} retries")
                return []
    
    return []
```

## Monitoring & Metrics

```python
from datetime import datetime
from typing import Dict

class DiarizationMetrics:
    """Track diarization performance"""
    
    def __init__(self):
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.total_time = 0.0
    
    async def diarize_with_metrics(
        self,
        service: DiarizationService,
        audio_path: str
    ) -> List[Dict]:
        """Execute diarization and record metrics"""
        import time
        
        self.total_calls += 1
        start = time.time()
        
        try:
            result = await service.diarize(audio_path)
            if result:
                self.successful_calls += 1
            else:
                self.failed_calls += 1
            return result
        except Exception as e:
            self.failed_calls += 1
            raise
        finally:
            elapsed = time.time() - start
            self.total_time += elapsed
            logger.info(f"Diarization took {elapsed:.2f}s")
    
    def get_stats(self) -> Dict:
        """Get performance statistics"""
        success_rate = (self.successful_calls / self.total_calls * 100
                       if self.total_calls > 0 else 0)
        avg_time = (self.total_time / self.total_calls
                   if self.total_calls > 0 else 0)
        
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": f"{success_rate:.1f}%",
            "average_time": f"{avg_time:.2f}s"
        }
```

---

**Next Steps**:
1. Copy these patterns into your codebase as needed
2. Add unit tests for your specific use cases
3. Monitor logs and metrics in production
4. Optimize based on performance data

See [DIARIZATION_SETUP.md](../DIARIZATION_SETUP.md) for full setup guide.
