# Speaker Diarization Setup Guide

This document covers the implementation and configuration of pyannote speaker diarization in the AI Meeting Assistant backend.

## Overview

The diarization service uses the `pyannote/speaker-diarization-3.1` model to identify and label different speakers in audio meetings. The implementation includes:

✅ **Singleton Pattern** - Model loaded once at first use (lazy initialization)  
✅ **GPU/CPU Support** - Automatic device detection  
✅ **Error Handling** - Non-blocking failures that don't crash the backend  
✅ **Comprehensive Logging** - Track loading, success, and failure events  
✅ **Production-Ready** - Thread-safe and optimized for deployment  

## Prerequisites

### 1. Get HuggingFace Token

The pyannote.audio model is gated on HuggingFace (requires agreement).

1. Visit: https://huggingface.co/pyannote/speaker-diarization-3.1
2. Read and accept the license/usage terms
3. Go to: https://huggingface.co/settings/tokens
4. Create or copy your API token (format: `YOUR_HF_TOKEN...`)

### 2. Install Dependencies

All required packages are in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Key packages:
- `pyannote.audio==3.1.1` - Diarization model
- `torch==2.1.2` & `torchaudio==2.1.2` - Deep learning
- `transformers==4.37.2` - Model loading
- `python-dotenv==1.0.0` - Environment variables

## Configuration

### Update `.env` File

Create or update `backend/.env` with your HuggingFace token:

```env
# HuggingFace API Token for gated models (pyannote.audio)
# Get token from: https://huggingface.co/settings/tokens
YOUR_HF_TOKEN=YOUR_HF_TOKEN

# Optional: Device selection (auto-detected if not specified)
# WHISPER_DEVICE=cuda  # Use GPU if available
```

**Security Note**: Never commit `.env` to version control. Add it to `.gitignore`:

```gitignore
backend/.env
```

### Configuration in `app/config.py`

The config automatically loads the YOUR_HF_TOKEN from `.env`:

```python
class Settings(BaseSettings):
    YOUR_HF_TOKEN: str | None = None  # Loaded from .env
    DIARIZATION_MODEL: str = "pyannote/speaker-diarization-3.1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

## Implementation Details

### Singleton Pattern

The `DiarizationService` uses a singleton pattern to ensure the model is loaded only once:

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
```

**Benefits**:
- Model loaded once at first use (lazy initialization)
- Saves memory and startup time
- Thread-safe access via lock
- No FastAPI startup blocking

### Lazy Loading

The model is NOT loaded during FastAPI startup. Instead:

1. First diarization call triggers `_load_pipeline()`
2. If YOUR_HF_TOKEN is missing, graceful failure with clear error log
3. If loading fails, backend continues working (diarization just skipped)

### GPU/CPU Handling

Automatic device selection:

```python
def _get_device(self) -> str:
    if torch.cuda.is_available():
        device = "cuda"
        logger.info(f"GPU available: {torch.cuda.get_device_name(0)}")
    else:
        device = "cpu"
        logger.info("GPU not available, using CPU for diarization")
    return device
```

Model is moved to the selected device after loading.

### Error Handling

The `diarize()` method has comprehensive error handling:

```python
async def diarize(self, audio_path: str) -> List[Dict]:
    try:
        if not self._load_pipeline():
            logger.warning("Pipeline load failed, returning empty diarization")
            return []
        
        diarization = self.pipeline(audio_path)
        # Process results...
        
    except Exception as e:
        logger.error(f"Diarization failed: {str(e)}", exc_info=True)
        logger.warning("Continuing without diarization...")
        return []
```

**Key points**:
- Returns empty list `[]` on failure (not an exception)
- Backend continues processing (transcription, summary, action items)
- Detailed error logged with full traceback
- User gets partial response (no speaker info, but other data intact)

### API Integration

The upload endpoint now safely calls diarization:

```python
@router.post("/meetings/upload", response_model=MeetingResponse)
async def upload_meeting(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # ... transcription ...
    
    # Speaker diarization (optional, safe to fail)
    logger.info("Starting speaker diarization...")
    diarization = await diarization_service.diarize(file_path)
    
    if diarization:
        logger.info(f"Diarization successful: {len(diarization)} speaker segments")
    else:
        logger.warning("Diarization returned empty results or failed gracefully")
    
    # Continue with transcription merging, summary, action items...
```

### Output Format

Diarization returns a list of speaker segments:

```python
[
    {
        "start": 0.0,          # Segment start time (seconds)
        "end": 5.2,            # Segment end time (seconds)
        "speaker": "Speaker_1", # Speaker label
        "duration": 5.2        # Duration (seconds)
    },
    {
        "start": 5.3,
        "end": 12.8,
        "speaker": "Speaker_2",
        "duration": 7.5
    }
]
```

### Transcription Merging

Diarization segments are merged with transcription:

```python
def merge_transcription_diarization(transcription, diarization):
    # Maps diarization speakers to transcription segments
    # If diarization fails, uses "Speaker_0" as fallback
    for segment in transcription["segments"]:
        # Find matching diarization segment by time overlap
        speaker = find_speaker_for_segment(segment, diarization)
        segments_with_speakers.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"],
            "speaker": speaker
        })
```

## API Response

When diarization succeeds:

```json
{
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "meeting.wav",
  "transcription": {
    "full_text": "Welcome to the meeting...",
    "segments": [
      {
        "start": 0.0,
        "end": 3.2,
        "text": "Welcome to the meeting",
        "speaker": "Speaker_1"
      },
      {
        "start": 3.5,
        "end": 8.1,
        "text": "Thanks for joining",
        "speaker": "Speaker_2"
      }
    ],
    "language": "en"
  },
  "summary": "The team discussed project updates...",
  "action_items": [
    {
      "item": "Schedule follow-up meeting",
      "responsible": "John",
      "due_date": "2025-02-05"
    }
  ],
  "duration": 45.3
}
```

When diarization fails (graceful):

```json
{
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "meeting.wav",
  "transcription": {
    "full_text": "Welcome to the meeting...",
    "segments": [
      {
        "start": 0.0,
        "end": 3.2,
        "text": "Welcome to the meeting",
        "speaker": "Speaker_0"  // Fallback speaker
      },
      {
        "start": 3.5,
        "end": 8.1,
        "text": "Thanks for joining",
        "speaker": "Speaker_0"  // Fallback speaker
      }
    ],
    "language": "en"
  },
  "summary": "The team discussed project updates...",
  "action_items": [...],
  "duration": 45.3
}
```

Backend still returns transcription, summary, and action items even if diarization fails.

## Logging

### Log Levels

**INFO** - Normal operation:
```
INFO:services.diarization:DiarizationService initialized (lazy-load mode, device: cpu)
INFO:services.diarization:GPU available: NVIDIA GeForce RTX 4090
INFO:services.diarization:Loading pyannote/speaker-diarization-3.1 (this may take a moment)...
INFO:services.diarization:Diarization pipeline loaded successfully on cuda
INFO:services.diarization:Starting speaker diarization for: uploads/meeting.wav
INFO:services.diarization:Diarization completed: 3 speaker segments detected
```

**WARNING** - Issues but continuing:
```
WARNING:services.diarization:YOUR_HF_TOKEN not configured. Set YOUR_HF_TOKEN in .env file...
WARNING:services.diarization:Diarization returned empty results or failed gracefully
WARNING:app.api:Diarization returned empty results, using generic speaker labels
```

**ERROR** - Failures:
```
ERROR:services.diarization:Failed to load diarization pipeline: [error details]
ERROR:services.diarization:Diarization processing failed: [error details]
ERROR:services.diarization:Audio file not found: /path/to/file.wav
```

### Debugging

Check diarization status via the service:

```python
status = diarization_service.get_status()
# {
#   "available": true,
#   "device": "cuda",
#   "YOUR_HF_TOKEN": true,
#   "model": "pyannote/speaker-diarization-3.1"
# }
```

## Troubleshooting

### Issue: "YOUR_HF_TOKEN not configured"

**Solution**: 
1. Get token from https://huggingface.co/settings/tokens
2. Add to `backend/.env`: `YOUR_HF_TOKEN=YOUR_HF_TOKEN`
3. Restart backend

### Issue: "Diarization model not available"

**Solution**:
1. Visit: https://huggingface.co/pyannote/speaker-diarization-3.1
2. Accept the usage agreement (click "Access repository")
3. Verify your HF token in `.env` is correct

### Issue: Out of Memory (OOM)

**Solution** (for GPU):
```python
# In services/diarization.py, add batch processing or:
# Use smaller model or CPU mode
DIARIZATION_MODEL=pyannote/speaker-diarization-3.0  # Older, lighter model
```

### Issue: Slow diarization on CPU

**Solution**:
- Use GPU if available: Install CUDA and verify with `torch.cuda.is_available()`
- For long files: Consider splitting audio into chunks (not implemented yet)

### Issue: Transcription and summary work, but diarization fails silently

**Solution**:
1. Check backend logs for error messages
2. Verify `YOUR_HF_TOKEN` is correct: `huggingface-cli login YOUR_HF_TOKEN`
3. Check internet connection (model download from HuggingFace)
4. Try manually loading: 
   ```python
   from pyannote.audio import Pipeline
   pipeline = Pipeline.from_pretrained(
       "pyannote/speaker-diarization-3.1",
       use_auth_token="YOUR_HF_TOKEN"
   )
   ```

## Performance Tips

1. **GPU Usage**: 
   - With NVIDIA GPU: ~2-3 seconds per minute of audio
   - With CPU: ~10-20 seconds per minute of audio

2. **Memory**:
   - GPU model: ~800 MB VRAM
   - CPU model: ~2 GB RAM

3. **Optimization**:
   - Already uses lazy loading (model not loaded until first use)
   - Singleton ensures only one model instance
   - Device automatically selected

4. **Scaling**:
   - Use GPU for production deployments
   - Consider Redis caching for repeated audio processing
   - For very long files: implement audio chunking

## Testing

### Manual Test

```python
import asyncio
from services.diarization import DiarizationService

async def test():
    service = DiarizationService()
    result = await service.diarize("path/to/audio.wav")
    print(result)

asyncio.run(test())
```

### API Test

```bash
curl -X POST http://localhost:8000/api/v1/meetings/upload \
  -F "file=@meeting.wav"
```

## Production Checklist

- [ ] YOUR_HF_TOKEN configured in `.env`
- [ ] `.env` file in `.gitignore`
- [ ] Backend restarted after `.env` changes
- [ ] GPU available and CUDA properly installed (optional but recommended)
- [ ] Error logs monitored for diarization failures
- [ ] Test with various audio formats and lengths
- [ ] Verify transcription works if diarization fails

## Security Notes

1. **Never commit `.env`** - Keep HF token private
2. **Token rotation** - If token is leaked, generate new one at https://huggingface.co/settings/tokens
3. **API keys** - If deploying publicly, use environment variables in deployment platform (Docker, Kubernetes, etc.)
4. **Audio files** - Ensure cleanup after processing (implemented in background task)

## References

- pyannote.audio: https://github.com/pyannote/pyannote-audio
- HuggingFace Model Card: https://huggingface.co/pyannote/speaker-diarization-3.1
- Pyannote Docs: https://pyannote.github.io/

---

**Last Updated**: January 29, 2025
**Implementation**: Python 3.10+, FastAPI 0.109+, PyTorch 2.1+
