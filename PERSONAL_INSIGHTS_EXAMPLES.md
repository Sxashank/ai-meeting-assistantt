# Personalized Meeting Intelligence - Code Examples & Implementation Details

## PersonalInsightsService Implementation

### Core Class Structure

```python
class PersonalInsightsService:
    """Extract personalized meeting insights for a specific user."""
    
    def __init__(self):
        self.name_placeholder_regex = re.compile(r'\b(you|your|assigned to you|for you)\b', re.IGNORECASE)
        logger.info("PersonalInsightsService initialized")
```

### Main Method: extract_personal_insights()

```python
async def extract_personal_insights(
    self,
    user_name: str,
    full_transcript: str,
    segments: List[Dict[str, Any]],
    action_items: List[Dict[str, Any]],
    diarization_available: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Main entry point for personal insights extraction.
    
    Returns:
        Dict with personal_summary, personal_transcript, assigned_tasks
        or None if extraction fails
    """
    # Validate input
    if not user_name or not user_name.strip():
        logger.warning("User name is empty, skipping")
        return None

    # Extract components
    personal_transcript_text, personal_segments = self._extract_personal_transcript(
        user_name, segments, diarization_available
    )
    
    personal_summary = await self._generate_personal_summary(
        personal_transcript_text, user_name
    )
    
    personal_action_items = self._extract_personal_action_items(
        user_name, action_items, personal_transcript_text
    )
    
    # Return structured insights
    return {
        "name": user_name,
        "personal_summary": personal_summary,
        "personal_transcript": personal_transcript_text,
        "personal_segments": personal_segments,
        "assigned_tasks": personal_action_items,
        "transcript_coverage": len(personal_segments),
        "action_items_count": len(personal_action_items)
    }
```

### Name Variations Generation

```python
def _generate_name_variations(self, name: str) -> List[str]:
    """
    Generate variations of a name for matching.
    
    Examples:
        "Shashank Kumar" → ["shashank kumar", "shashank", "sk"]
        "John" → ["john"]
    """
    variations = set()
    name_lower = name.lower()
    variations.add(name_lower)

    # Add first name if multi-word
    parts = name.split()
    if len(parts) > 1:
        variations.add(parts[0].lower())

    # Add initials
    initials = "".join([p[0] for p in parts if p])
    if len(initials) > 0:
        variations.add(initials.lower())

    return list(variations)
```

### Transcript Extraction (Dual Strategy)

```python
def _extract_personal_transcript(
    self,
    user_name: str,
    segments: List[Dict[str, Any]],
    diarization_available: bool
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Extract segments relevant to user using two strategies.
    
    Strategy 1: Speaker matching (if diarization available)
    Strategy 2: Name mention in text (always)
    """
    personal_segments = []
    seen_texts = set()

    name_lower = user_name.lower()
    name_variations = self._generate_name_variations(user_name)

    for segment in segments:
        segment_text = segment.get("text", "").strip()
        if not segment_text:
            continue

        is_match = False
        match_reason = None

        # Strategy 1: Speaker-based matching
        if diarization_available:
            speaker = segment.get("speaker", "").lower()
            if self._is_user_speaker(speaker, name_lower):
                is_match = True
                match_reason = "speaker_match"

        # Strategy 2: Name mention in text
        if not is_match:
            if self._contains_name_mention(segment_text, name_lower, name_variations):
                is_match = True
                match_reason = "name_mention"

        # Add if matched and not duplicate
        if is_match:
            if segment_text not in seen_texts:
                personal_segments.append({
                    **segment,
                    "match_reason": match_reason
                })
                seen_texts.add(segment_text)

    # Build concatenated transcript
    personal_transcript = " ".join([seg.get("text", "") for seg in personal_segments])

    return personal_transcript.strip(), personal_segments
```

### Name Mention Detection

```python
def _contains_name_mention(
    self,
    text: str,
    name_lower: str,
    name_variations: List[str]
) -> bool:
    """
    Check if text contains mention of user's name.
    
    Uses word boundaries to avoid partial matches:
        "Shashank" matches "Shashank"
        "Shashank" matches "Shashank Kumar"
        "Shashank" does NOT match "Shashankamaran"
    """
    text_lower = text.lower()

    for variation in name_variations:
        pattern = r'\b' + re.escape(variation) + r'\b'
        if re.search(pattern, text_lower):
            return True

    return False
```

### Speaker Identification

```python
def _is_user_speaker(self, speaker_label: str, name_lower: str) -> bool:
    """
    Check if speaker label corresponds to the user.
    
    Handles various formats:
        "Shashank" → True
        "Speaker_1_Shashank" → True
        "Speaker_0" → False (generic)
    """
    speaker_lower = speaker_label.lower()
    
    # Direct name match in speaker label
    if name_lower in speaker_lower:
        return True
    
    return False
```

### Personal Summary Generation

```python
async def _generate_personal_summary(
    self,
    personal_transcript: str,
    user_name: str
) -> str:
    """
    Generate personalized summary from personal transcript.
    
    Shorter summary (150 chars) focused on user's involvement.
    """
    if not personal_transcript or len(personal_transcript) < 10:
        logger.warning(f"Personal transcript too short for {user_name}")
        return ""

    try:
        context_prompt = f"Summary for {user_name}'s involvement in the meeting:\n"
        
        summary_result = await summarization_service.summarize(
            personal_transcript,
            max_length=150,  # Shorter for personal context
            min_length=30
        )

        summary_text = (summary_result.get("summary", "") 
                       if isinstance(summary_result, dict) 
                       else str(summary_result))

        return context_prompt + summary_text if summary_text else ""

    except Exception as e:
        logger.error(f"Error generating personal summary: {str(e)}", exc_info=True)
        return ""
```

### Action Item Extraction

```python
def _extract_personal_action_items(
    self,
    user_name: str,
    action_items: List[Dict[str, Any]],
    personal_transcript: str
) -> List[Dict[str, Any]]:
    """
    Extract action items assigned to or relevant to user.
    
    Two-pronged approach:
    1. Direct assignee matching
    2. Item mentioned in personal transcript
    """
    personal_items = []
    name_lower = user_name.lower()
    name_variations = self._generate_name_variations(user_name)
    personal_transcript_lower = personal_transcript.lower()

    for item in action_items:
        is_relevant = False

        # Strategy 1: Direct assignee match
        assignee = item.get("assignee", "").lower()
        if assignee:
            for variation in name_variations:
                if variation in assignee:
                    is_relevant = True
                    break

        # Strategy 2: Item mentioned in personal transcript
        if not is_relevant:
            task_text = item.get("task", "").lower()
            context = item.get("context", "").lower()
            
            if (task_text and task_text in personal_transcript_lower) or \
               (context and context in personal_transcript_lower):
                is_relevant = True

        if is_relevant:
            personal_items.append(item)

    return personal_items
```

## API Integration Example

### Endpoint Handler

```python
@router.post("/meetings/upload", response_model=MeetingResponse)
async def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_name: str = Query(None, description="Optional user name for personalized insights")
):
    """Process meeting and extract personalized insights if user_name provided."""
    
    try:
        # Standard processing...
        transcription = await transcription_service.transcribe(audio_data)
        diarization = await diarization_service.diarize(file_path)
        transcript_with_speakers = merge_transcription_diarization(transcription, diarization)
        summary = await summarization_service.summarize(transcript_with_speakers["full_text"])
        action_items = await action_item_extractor.extract(transcript_with_speakers["full_text"])

        # NEW: Personal insights extraction
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

        response = {
            "meeting_id": meeting_id,
            "filename": file.filename,
            "transcription": transcript_with_speakers,
            "summary": summary,
            "action_items": action_items,
            "duration": audio_processor.get_duration(audio_data),
            "personal_insights": personal_insights  # Include in response
        }

        return response

    except Exception as e:
        logger.error(f"Error processing meeting: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

## Client Usage Examples

### Python Client

```python
import requests
import json

# Upload with personal insights
response = requests.post(
    "http://localhost:8000/api/v1/meetings/upload",
    files={"file": open("meeting.wav", "rb")},
    params={"user_name": "Shashank"}
)

data = response.json()

# Access personal insights
if data["personal_insights"]:
    insights = data["personal_insights"]
    print(f"User: {insights['name']}")
    print(f"Summary: {insights['personal_summary']}")
    print(f"Transcript: {insights['personal_transcript']}")
    print(f"Tasks: {len(insights['assigned_tasks'])} tasks assigned")
    
    for task in insights['assigned_tasks']:
        print(f"  - {task['task']} (due {task['deadline']})")
else:
    print("No personal insights available")
```

### cURL Examples

```bash
# With personalization
curl -X POST http://localhost:8000/api/v1/meetings/upload \
  -F "file=@meeting.wav" \
  -F "user_name=Shashank" | jq '.personal_insights'

# Extract only personal summary
curl -X POST http://localhost:8000/api/v1/meetings/upload \
  -F "file=@meeting.wav" \
  -F "user_name=Alice" | jq '.personal_insights.personal_summary'

# Extract assigned tasks
curl -X POST http://localhost:8000/api/v1/meetings/upload \
  -F "file=@meeting.wav" \
  -F "user_name=John" | jq '.personal_insights.assigned_tasks'
```

## Error Handling Patterns

### Safe Extraction

```python
async def safe_extract_personal_insights(
    user_name: str,
    segments: List[Dict],
    action_items: List[Dict]
) -> Optional[Dict]:
    """Safely extract with comprehensive error handling."""
    
    # Input validation
    if not user_name or not isinstance(user_name, str):
        logger.warning(f"Invalid user_name: {user_name}")
        return None
    
    try:
        # Attempt extraction
        result = await personal_insights_service.extract_personal_insights(
            user_name, segments, action_items, diarization_available=True
        )
        
        # Validate result
        if result and result.get("personal_transcript"):
            return result
        else:
            logger.info(f"No personal insights found for {user_name}")
            return None
            
    except Exception as e:
        logger.error(f"Personal insights extraction failed: {str(e)}", exc_info=True)
        return None  # Return None, don't crash
```

## Testing Examples

### Unit Test

```python
import pytest
from services.personal_insights import PersonalInsightsService

@pytest.mark.asyncio
async def test_personal_insights_extraction():
    service = PersonalInsightsService()
    
    segments = [
        {"text": "Shashank: Let's start", "speaker": "Speaker_1", "start": 0, "end": 2},
        {"text": "John: Agreed", "speaker": "Speaker_2", "start": 3, "end": 4},
        {"text": "Shashank: I'll prepare the report", "speaker": "Speaker_1", "start": 5, "end": 7},
    ]
    
    action_items = [
        {
            "task": "Prepare report",
            "assignee": "Shashank",
            "deadline": "2025-02-15",
            "priority": "high",
            "context": "Discussed in meeting",
            "confidence": 0.95
        }
    ]
    
    result = await service.extract_personal_insights(
        user_name="Shashank",
        full_transcript="Shashank: Let's start. John: Agreed. Shashank: I'll prepare.",
        segments=segments,
        action_items=action_items,
        diarization_available=True
    )
    
    assert result is not None
    assert result["name"] == "Shashank"
    assert len(result["personal_segments"]) == 2
    assert len(result["assigned_tasks"]) == 1
    assert "Let's start" in result["personal_transcript"]
```

### Integration Test

```python
async def test_api_with_personalization():
    """Test API with personalized insights."""
    
    # Upload with user name
    with open("test_meeting.wav", "rb") as f:
        response = await client.post(
            "/api/v1/meetings/upload",
            files={"file": f},
            params={"user_name": "Alice"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["personal_insights"] is not None
    assert data["personal_insights"]["name"] == "Alice"
    assert "personal_summary" in data["personal_insights"]
    assert "personal_transcript" in data["personal_insights"]
    assert "assigned_tasks" in data["personal_insights"]
```

## Performance Optimization

### Caching Name Variations

```python
class OptimizedPersonalInsightsService(PersonalInsightsService):
    def __init__(self):
        super().__init__()
        self._name_cache = {}  # Cache variations
    
    def _generate_name_variations(self, name: str) -> List[str]:
        """Cache name variations for performance."""
        if name in self._name_cache:
            return self._name_cache[name]
        
        variations = super()._generate_name_variations(name)
        self._name_cache[name] = variations
        return variations
```

### Batch Processing

```python
async def process_multiple_users(
    users: List[str],
    segments: List[Dict],
    action_items: List[Dict]
) -> Dict[str, Optional[Dict]]:
    """Extract insights for multiple users efficiently."""
    
    results = {}
    for user in users:
        insights = await personal_insights_service.extract_personal_insights(
            user_name=user,
            full_transcript=" ".join([s.get("text", "") for s in segments]),
            segments=segments,
            action_items=action_items
        )
        results[user] = insights
    
    return results
```

---

Ready to integrate! Check the main implementation file at `backend/services/personal_insights.py`
