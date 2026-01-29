import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from services.summarization import SummarizationService

logger = logging.getLogger(__name__)

summarization_service = SummarizationService()


class PersonalInsightsService:
    """
    Extract personalized meeting insights for a specific user.
    
    Features:
    - Extract personal transcript by name mention or speaker label
    - Generate personalized summary
    - Extract action items assigned to the user
    - Works with or without diarization
    - Case-insensitive matching
    - Production-safe with error handling
    """

    def __init__(self):
        self.name_placeholder_regex = re.compile(r'\b(you|your|assigned to you|for you)\b', re.IGNORECASE)
        logger.info("PersonalInsightsService initialized")

    async def extract_personal_insights(
        self,
        user_name: str,
        full_transcript: str,
        segments: List[Dict[str, Any]],
        action_items: List[Dict[str, Any]],
        diarization_available: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Extract personalized insights for a given user.
        
        Args:
            user_name: Name of the user (e.g., "Shashank")
            full_transcript: Complete meeting transcript text
            segments: Transcription segments with speaker labels
            action_items: Extracted action items from meeting
            diarization_available: Whether speaker diarization is available
            
        Returns:
            Dict with personal_summary, personal_transcript, assigned_tasks
            or None if extraction fails
        """
        if not user_name or not user_name.strip():
            logger.warning("User name is empty, skipping personal insights extraction")
            return None

        try:
            logger.info(f"Extracting personal insights for: {user_name}")

            # Extract personal transcript (combines name mentions + speaker label matches)
            personal_transcript_text, personal_segments = self._extract_personal_transcript(
                user_name, segments, diarization_available
            )

            if not personal_transcript_text:
                logger.warning(f"No personal transcript found for {user_name}")
                return None

            # Generate personalized summary
            personal_summary = await self._generate_personal_summary(
                personal_transcript_text, user_name
            )

            # Extract personalized action items
            personal_action_items = self._extract_personal_action_items(
                user_name, action_items, personal_transcript_text
            )

            insights = {
                "name": user_name,
                "personal_summary": personal_summary,
                "personal_transcript": personal_transcript_text,
                "personal_segments": personal_segments,
                "assigned_tasks": personal_action_items,
                "transcript_coverage": len(personal_segments),
                "action_items_count": len(personal_action_items)
            }

            logger.info(
                f"Personal insights extracted for {user_name}: "
                f"{len(personal_segments)} segments, "
                f"{len(personal_action_items)} tasks"
            )
            return insights

        except Exception as e:
            logger.error(
                f"Error extracting personal insights for {user_name}: {str(e)}",
                exc_info=True
            )
            return None

    def _extract_personal_transcript(
        self,
        user_name: str,
        segments: List[Dict[str, Any]],
        diarization_available: bool
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extract transcript segments relevant to the user.
        
        Uses two strategies:
        1. If diarization available: Match by speaker identification
        2. Always: Match by name mentions in text
        
        Returns:
            (personal_transcript_text, personal_segments_list)
        """
        personal_segments = []
        seen_texts = set()  # Avoid duplicates

        # Normalize user name for matching
        name_lower = user_name.lower()
        name_variations = self._generate_name_variations(user_name)

        logger.debug(f"Looking for name variations: {name_variations}")

        for segment in segments:
            segment_text = segment.get("text", "").strip()
            if not segment_text:
                continue

            is_match = False
            match_reason = None

            # Strategy 1: Speaker-based matching (if diarization available)
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

            # Add segment if matched and not duplicate
            if is_match:
                if segment_text not in seen_texts:
                    personal_segments.append({
                        **segment,
                        "match_reason": match_reason
                    })
                    seen_texts.add(segment_text)

        # Build concatenated personal transcript
        personal_transcript = " ".join([seg.get("text", "") for seg in personal_segments])

        logger.debug(
            f"Extracted {len(personal_segments)} personal segments for {user_name}"
        )

        return personal_transcript.strip(), personal_segments

    def _generate_name_variations(self, name: str) -> List[str]:
        """Generate variations of a name for matching."""
        variations = set()
        name_lower = name.lower()
        variations.add(name_lower)

        # Add first name if it's multi-word
        parts = name.split()
        if len(parts) > 1:
            variations.add(parts[0].lower())

        # Add initials
        initials = "".join([p[0] for p in parts if p])
        if len(initials) > 0:
            variations.add(initials.lower())

        return list(variations)

    def _contains_name_mention(
        self,
        text: str,
        name_lower: str,
        name_variations: List[str]
    ) -> bool:
        """Check if text contains mention of the user's name."""
        text_lower = text.lower()

        # Direct name matches
        for variation in name_variations:
            # Use word boundary to avoid partial matches
            pattern = r'\b' + re.escape(variation) + r'\b'
            if re.search(pattern, text_lower):
                return True

        return False

    def _is_user_speaker(self, speaker_label: str, name_lower: str) -> bool:
        """
        Check if speaker label corresponds to the user.
        
        Handles cases like:
        - speaker = "Shashank"
        - speaker = "Speaker_1_Shashank"
        - speaker = "Speaker_0"
        """
        speaker_lower = speaker_label.lower()

        # Direct name match in speaker label
        if name_lower in speaker_lower:
            return True

        # If user name contains speaker ID (e.g., "Shashank Speaker_1")
        # This would be a custom mapping set during diarization
        return False

    async def _generate_personal_summary(
        self,
        personal_transcript: str,
        user_name: str
    ) -> str:
        """
        Generate a personalized summary for the user.
        
        Uses the same transformer pipeline but focused on personal context.
        """
        if not personal_transcript or len(personal_transcript) < 10:
            logger.warning(f"Personal transcript too short for {user_name}: {len(personal_transcript)} chars")
            return ""

        try:
            # Prepend context to summary for personalization
            context_prompt = f"Summary for {user_name}'s involvement in the meeting:\n"
            
            summary_result = await summarization_service.summarize(
                personal_transcript,
                max_length=150,  # Shorter summary for personal context
                min_length=30
            )

            # Extract summary text from result
            if isinstance(summary_result, dict):
                summary_text = summary_result.get("summary", "")
            else:
                summary_text = str(summary_result)

            return context_prompt + summary_text if summary_text else ""

        except Exception as e:
            logger.error(
                f"Error generating personal summary for {user_name}: {str(e)}",
                exc_info=True
            )
            return ""

    def _extract_personal_action_items(
        self,
        user_name: str,
        action_items: List[Dict[str, Any]],
        personal_transcript: str
    ) -> List[Dict[str, Any]]:
        """
        Extract action items assigned to or relevant to the user.
        
        Uses multiple strategies:
        1. Direct assignee matching
        2. Action items mentioned in personal transcript
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
                
                if task_text and task_text in personal_transcript_lower:
                    is_relevant = True
                elif context and context in personal_transcript_lower:
                    is_relevant = True

            if is_relevant:
                personal_items.append(item)

        logger.debug(
            f"Extracted {len(personal_items)} personal action items for {user_name}"
        )

        return personal_items

    def get_status(self) -> Dict:
        """Get service status for debugging."""
        return {
            "available": True,
            "service": "PersonalInsightsService",
            "features": [
                "speaker_matching",
                "name_mention_extraction",
                "personalized_summary",
                "assigned_tasks_extraction"
            ]
        }
