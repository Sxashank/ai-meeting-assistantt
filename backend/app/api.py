from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
import uuid
from pathlib import Path
import logging

from app.config import settings
from services.transcription import TranscriptionService
from services.summarization import SummarizationService
from services.action_items import ActionItemExtractor
from services.diarization import DiarizationService
from services.personal_insights import PersonalInsightsService
from services.mention_tracker import MentionTracker
from utils.audio_processing import AudioProcessor
from utils.file_handler import FileHandler
from models.schemas import MeetingResponse

logger = logging.getLogger(__name__)
router = APIRouter()

transcription_service = TranscriptionService()
summarization_service = SummarizationService()
action_item_extractor = ActionItemExtractor()
diarization_service = DiarizationService()  # Singleton instance
personal_insights_service = PersonalInsightsService()  # Personal insights extractor
mention_tracker = MentionTracker()  # Mention tracking service
audio_processor = AudioProcessor()
file_handler = FileHandler()


@router.post("/meetings/upload", response_model=MeetingResponse)
async def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_name: str = Query(None, description="Optional user name for personalized insights")
):
    """
    Process audio meeting file: transcription, diarization, summarization, action items, and personalized insights.
    
    Args:
        file: Audio file to process
        user_name: Optional name of the user for personalized insights (e.g., "Shashank")
    """
    try:
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in settings.ALLOWED_AUDIO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"File format not supported. Allowed: {settings.ALLOWED_AUDIO_FORMATS}"
            )

        meeting_id = str(uuid.uuid4())

        file_path = await file_handler.save_upload(file, meeting_id)
        logger.info(f"Saved audio file: {file_path}")

        audio_data = audio_processor.load_audio(file_path)

        # Transcription (required)
        logger.info("Starting transcription...")
        transcription = await transcription_service.transcribe(audio_data)

        # Speaker diarization (optional, safe to fail)
        logger.info("Starting speaker diarization...")
        diarization = await diarization_service.diarize(file_path)

        if diarization:
            logger.info(f"Diarization successful: {len(diarization)} speaker segments detected")
        else:
            logger.warning("Diarization returned empty results or failed gracefully")

        # Merge transcription with diarization info
        transcript_with_speakers = merge_transcription_diarization(
            transcription, diarization
        )

        # Summarization (required)
        logger.info("Generating summary...")
        summary = await summarization_service.summarize(
            transcript_with_speakers["full_text"]
        )

        # Action items extraction (required)
        logger.info("Extracting action items...")
        action_items = await action_item_extractor.extract(
            transcript_with_speakers["full_text"]
        )

        # Personal insights extraction (optional, if user_name provided)
        personal_insights = None
        if user_name:
            logger.info(f"Extracting personal insights for: {user_name}")
            personal_insights = await personal_insights_service.extract_personal_insights(
                user_name=user_name,
                full_transcript=transcript_with_speakers["full_text"],
                segments=transcript_with_speakers["segments"],
                action_items=action_items,
                diarization_available=bool(diarization)
            )
            if personal_insights:
                logger.info(f"Personal insights extracted successfully for {user_name}")
            else:
                logger.warning(f"No personal insights extracted for {user_name}")

        # Mention tracking (optional, if user_name provided)
        mention_tracking = None
        if user_name:
            logger.info(f"Tracking mentions for: {user_name}")
            mention_tracking = await mention_tracker.track_mentions(
                username=user_name,
                full_transcript=transcript_with_speakers["full_text"],
                segments=transcript_with_speakers["segments"],
                diarization_available=bool(diarization)
            )
            if mention_tracking:
                logger.info(f"Mention tracking complete for {user_name}: {mention_tracking.get('mention_count', 0)} mentions found")
            else:
                logger.info(f"No mentions found for {user_name}")

        response = {
            "meeting_id": meeting_id,
            "filename": file.filename,
            "transcription": transcript_with_speakers,
            "summary": summary,
            "action_items": action_items,
            "duration": audio_processor.get_duration(audio_data),
            "personal_insights": personal_insights,
            "mention_tracking": mention_tracking
        }

        background_tasks.add_task(file_handler.cleanup_file, file_path)

        return response

    except Exception as e:
        logger.error(f"Error processing meeting: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def merge_transcription_diarization(transcription, diarization):
    """
    Merge transcription segments with diarization speaker labels.
    If diarization is empty, assigns "Speaker_0" to all segments.
    """
    segments_with_speakers = []

    # If diarization is available, map speakers to segments
    if diarization:
        for segment in transcription["segments"]:
            segment_start = segment["start"]
            segment_end = segment["end"]

            # Find matching diarization segment
            speaker = "Speaker_0"  # Default fallback
            for dia_segment in diarization:
                # Check if segment overlaps with diarization
                if (dia_segment["start"] < segment_end and
                    dia_segment["end"] > segment_start):
                    speaker = dia_segment["speaker"]
                    break

            segments_with_speakers.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"],
                "speaker": speaker
            })
    else:
        # Fallback: use generic speaker labels if no diarization
        logger.debug("No diarization data available, using generic speaker labels")
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
