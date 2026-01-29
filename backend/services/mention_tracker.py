"""
Mention Tracker Service - Real-time tracking and highlighting of user mentions in meetings

Features:
- Case-insensitive name detection
- Context-aware highlighting
- Sentence extraction with mentions
- Task assignment NLP parsing
- Speaker integration
- Production-ready error handling
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class MentionTracker:
    """
    Tracks mentions of user names in transcripts and provides:
    - Highlighted transcript with mention tags
    - Sentence extraction
    - Mention statistics
    - Task assignments
    """

    def __init__(self):
        """Initialize the mention tracker service"""
        self.mention_count = 0
        self.logger = logger
        self.logger.info("MentionTracker service initialized")

    async def track_mentions(
        self,
        username: str,
        full_transcript: str,
        segments: List[Dict[str, Any]],
        diarization_available: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Track all mentions of a username in the transcript

        Args:
            username: Name to search for
            full_transcript: Full meeting transcript text
            segments: List of transcript segments with metadata
            diarization_available: Whether speaker diarization is available

        Returns:
            Dict with highlight_transcript, mention_count, sentences_with_mentions, etc.
        """
        try:
            if not username or not full_transcript:
                self.logger.warning("Empty username or transcript provided")
                return None

            username = username.strip()
            self.logger.info(f"Starting mention tracking for: {username}")

            # Generate name variations for matching
            name_variations = self._generate_name_variations(username)
            self.logger.debug(f"Name variations: {name_variations}")

            # Find all mentions with context
            mentions = self._find_mentions(full_transcript, name_variations)
            self.logger.info(f"Found {len(mentions)} mentions of {username}")

            if not mentions:
                self.logger.info(f"No mentions found for {username}")
                return None

            # Build highlighted transcript
            highlighted_transcript = self._build_highlighted_transcript(
                full_transcript, mentions
            )

            # Extract sentences containing mentions
            sentences_with_mentions = self._extract_sentences_with_mentions(
                full_transcript, mentions
            )

            # Extract task assignments
            assigned_tasks = self._extract_task_assignments(
                sentences_with_mentions, username, name_variations
            )

            # Get speaker context if available
            speaker_mentions = []
            if diarization_available:
                speaker_mentions = self._get_speaker_mentions(
                    segments, name_variations
                )

            # Compile results
            result = {
                "username": username,
                "highlight_transcript": highlighted_transcript,
                "mention_count": len(mentions),
                "mentions": mentions,
                "sentences_with_mentions": sentences_with_mentions,
                "sentence_count": len(sentences_with_mentions),
                "assigned_tasks": assigned_tasks,
                "speaker_mentions": speaker_mentions,
                "tracked_at": datetime.now().isoformat(),
                "tracking_status": "success"
            }

            self.logger.info(f"Mention tracking complete for {username}")
            return result

        except Exception as e:
            self.logger.error(f"Error tracking mentions: {str(e)}", exc_info=True)
            return None

    def _generate_name_variations(self, username: str) -> List[str]:
        """
        Generate variations of the username for matching

        Args:
            username: Original username

        Returns:
            List of name variations
        """
        variations = [username.lower()]

        # Add first name if multi-word
        if " " in username:
            first_name = username.split()[0].lower()
            variations.append(first_name)

            # Add initials
            initials = "".join([word[0] for word in username.split()]).lower()
            variations.append(initials)

        return list(set(variations))

    def _find_mentions(
        self,
        transcript: str,
        name_variations: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Find all mentions of name variations in transcript

        Args:
            transcript: Full transcript text
            name_variations: List of name patterns to search for

        Returns:
            List of mention dictionaries with position and context
        """
        mentions = []

        for variation in name_variations:
            # Create word-boundary regex to avoid partial matches
            pattern = r'\b' + re.escape(variation) + r'\b'

            for match in re.finditer(pattern, transcript, re.IGNORECASE):
                start_pos = match.start()
                end_pos = match.end()

                # Extract context (50 chars before and after)
                context_start = max(0, start_pos - 50)
                context_end = min(len(transcript), end_pos + 50)
                context = transcript[context_start:context_end]

                mention = {
                    "variation": variation,
                    "matched_text": match.group(),
                    "position": start_pos,
                    "end_position": end_pos,
                    "context": context.strip()
                }
                mentions.append(mention)

        # Remove duplicates and sort by position
        mentions = self._deduplicate_mentions(mentions)
        mentions.sort(key=lambda x: x["position"])

        return mentions

    def _deduplicate_mentions(
        self,
        mentions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove overlapping/duplicate mentions

        Args:
            mentions: List of mention dictionaries

        Returns:
            Deduplicated list
        """
        if not mentions:
            return []

        # Sort by position
        sorted_mentions = sorted(mentions, key=lambda x: x["position"])
        deduplicated = [sorted_mentions[0]]

        for mention in sorted_mentions[1:]:
            last = deduplicated[-1]
            # Skip if position overlaps
            if mention["position"] < last["end_position"] + 5:
                continue
            deduplicated.append(mention)

        return deduplicated

    def _build_highlighted_transcript(
        self,
        transcript: str,
        mentions: List[Dict[str, Any]]
    ) -> str:
        """
        Build transcript with highlighted mentions using tags

        Args:
            transcript: Original transcript
            mentions: List of mentions to highlight

        Returns:
            Transcript with [MENTION]name[/MENTION] tags
        """
        if not mentions:
            return transcript

        # Sort mentions by position in reverse to maintain positions
        sorted_mentions = sorted(mentions, key=lambda x: x["position"], reverse=True)

        highlighted = transcript
        for mention in sorted_mentions:
            start = mention["position"]
            end = mention["end_position"]
            matched_text = mention["matched_text"]

            # Insert highlighting tags
            before = highlighted[:start]
            after = highlighted[end:]
            highlighted = f"{before}[MENTION]{matched_text}[/MENTION]{after}"

        return highlighted

    def _extract_sentences_with_mentions(
        self,
        transcript: str,
        mentions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract full sentences containing name mentions

        Args:
            transcript: Full transcript
            mentions: List of mentions

        Returns:
            List of sentences with mention information
        """
        sentences = []

        # Split transcript into sentences
        # Handle common sentence endings
        sentence_pattern = r'(?<=[.!?])\s+|\n+'
        raw_sentences = re.split(sentence_pattern, transcript)

        current_pos = 0
        for raw_sentence in raw_sentences:
            if not raw_sentence.strip():
                current_pos += len(raw_sentence)
                continue

            sentence_start = current_pos
            sentence_end = current_pos + len(raw_sentence)

            # Check if any mention falls within this sentence
            sentence_mentions = [
                m for m in mentions
                if sentence_start <= m["position"] < sentence_end
            ]

            if sentence_mentions:
                sentence_dict = {
                    "sentence": raw_sentence.strip(),
                    "position": sentence_start,
                    "mention_count": len(sentence_mentions),
                    "mentions": [
                        {
                            "text": m["matched_text"],
                            "variation": m["variation"],
                            "position_in_sentence": m["position"] - sentence_start
                        }
                        for m in sentence_mentions
                    ]
                }
                sentences.append(sentence_dict)

            current_pos = sentence_end + 1

        return sentences

    def _extract_task_assignments(
        self,
        sentences: List[Dict[str, Any]],
        username: str,
        name_variations: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract task assignments using NLP patterns

        Args:
            sentences: Sentences containing mentions
            username: Username to match
            name_variations: Name variations

        Returns:
            List of extracted task assignments
        """
        tasks = []

        # Task assignment patterns
        task_patterns = [
            r'(?:can you|could you|will you|would you|can (?:' + '|'.join(name_variations) + r')|' + '|'.join(name_variations) + r'\s+(?:can|could|will|would))\s+(.+?)(?:[.!?]|$)',
            r'(?:assign|assigned|assign to|give to)\s+(?:' + '|'.join(name_variations) + r')\s+(?:the\s+)?task\s+(?:to\s+)?(.+?)(?:[.!?]|$)',
            r'(?:' + '|'.join(name_variations) + r')\s+(?:needs to|should|will|can|must)\s+(.+?)(?:[.!?]|$)',
            r'(?:needs|need)\s+(?:' + '|'.join(name_variations) + r')\s+to\s+(.+?)(?:[.!?]|$)',
        ]

        for sentence_dict in sentences:
            sentence_text = sentence_dict["sentence"]

            for pattern in task_patterns:
                matches = re.finditer(pattern, sentence_text, re.IGNORECASE)
                for match in matches:
                    task_text = match.group(1).strip()

                    if task_text and len(task_text) > 5:  # Filter very short matches
                        # Capitalize first letter
                        task_text = task_text[0].upper() + task_text[1:] if task_text else task_text

                        task = {
                            "task": task_text,
                            "assigned_to": username,
                            "source_sentence": sentence_text,
                            "confidence": "extracted"
                        }
                        tasks.append(task)

        # Remove duplicates
        unique_tasks = []
        seen = set()
        for task in tasks:
            task_key = task["task"].lower()
            if task_key not in seen:
                unique_tasks.append(task)
                seen.add(task_key)

        return unique_tasks

    def _get_speaker_mentions(
        self,
        segments: List[Dict[str, Any]],
        name_variations: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get mentions from speaker context if diarization available

        Args:
            segments: Transcript segments with speaker info
            name_variations: Name variations to match

        Returns:
            List of speaker mentions
        """
        speaker_mentions = []

        for segment in segments:
            if not segment.get("speaker"):
                continue

            speaker = segment["speaker"].lower()

            for variation in name_variations:
                if variation in speaker:
                    speaker_mention = {
                        "segment_index": segment.get("index", 0),
                        "speaker": segment["speaker"],
                        "text": segment.get("text", ""),
                        "start_time": segment.get("start", 0),
                        "end_time": segment.get("end", 0),
                        "mention_type": "speaker"
                    }
                    speaker_mentions.append(speaker_mention)
                    break

        return speaker_mentions

    def get_mention_statistics(
        self,
        track_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate statistics from tracking results

        Args:
            track_result: Result from track_mentions

        Returns:
            Statistics dictionary
        """
        if not track_result:
            return {}

        return {
            "total_mentions": track_result.get("mention_count", 0),
            "sentence_mentions": track_result.get("sentence_count", 0),
            "task_count": len(track_result.get("assigned_tasks", [])),
            "speaker_mentions": len(track_result.get("speaker_mentions", [])),
            "engagement_level": self._calculate_engagement(track_result)
        }

    def _calculate_engagement(self, track_result: Dict[str, Any]) -> str:
        """
        Calculate engagement level based on mentions

        Args:
            track_result: Tracking result

        Returns:
            Engagement level string
        """
        mention_count = track_result.get("mention_count", 0)

        if mention_count >= 20:
            return "high"
        elif mention_count >= 10:
            return "medium"
        elif mention_count >= 5:
            return "moderate"
        elif mention_count > 0:
            return "low"
        else:
            return "none"

    def format_for_display(
        self,
        track_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format tracking result for frontend display

        Args:
            track_result: Result from track_mentions

        Returns:
            Formatted dictionary for UI
        """
        if not track_result:
            return {}

        return {
            "username": track_result.get("username"),
            "highlighted_transcript": track_result.get("highlight_transcript"),
            "mention_count": track_result.get("mention_count", 0),
            "sentences_with_mentions": track_result.get("sentences_with_mentions", []),
            "assigned_tasks": track_result.get("assigned_tasks", []),
            "statistics": self.get_mention_statistics(track_result),
            "display_ready": True
        }

    def get_status(self) -> Dict[str, Any]:
        """Get service status for debugging"""
        return {
            "service": "MentionTracker",
            "status": "active",
            "version": "1.0",
            "features": [
                "mention_detection",
                "transcript_highlighting",
                "sentence_extraction",
                "task_assignment",
                "speaker_context",
                "engagement_metrics"
            ]
        }
