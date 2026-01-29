import spacy
import re
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ActionItemExtractor:
    def __init__(self):
        logger.info("Loading spaCy model...")
        self.nlp = spacy.load("en_core_web_sm")
        self.action_verbs = [
            "will", "should", "must", "need to", "needs to", "have to", "has to",
            "going to", "plan to", "plans to", "responsible for", "assigned to",
            "take care of", "handle", "complete", "finish", "deliver", "prepare",
            "create", "build", "develop", "design", "implement", "review", "send"
        ]
        self.priority_keywords = {
            "high": ["urgent", "asap", "immediately", "critical", "high priority"],
            "medium": ["important", "soon", "this week", "medium priority"],
            "low": ["when possible", "eventually", "low priority", "nice to have"]
        }
        self.date_patterns = [
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(tomorrow|today|next week|this week)\b',
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b',
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'
        ]
        logger.info("ActionItemExtractor initialized")
    
    async def extract(self, text: str) -> List[Dict]:
        try:
            logger.info("Extracting action items...")
            doc = self.nlp(text)
            action_items = []
            
            for sent in doc.sents:
                sentence_text = sent.text.strip()
                if not self._contains_action_verb(sentence_text):
                    continue
                
                assignee = self._extract_assignee(sent)
                deadline = self._extract_deadline(sentence_text)
                priority = self._extract_priority(sentence_text)
                task = self._extract_task_description(sentence_text)
                
                confidence = self._calculate_confidence(
                    has_assignee=assignee is not None,
                    has_deadline=deadline is not None,
                    has_action_verb=True,
                    sentence_length=len(sentence_text.split())
                )
                
                if confidence >= 0.6 and task:
                    action_items.append({
                        "task": task,
                        "assignee": assignee or "Unassigned",
                        "deadline": deadline or "No deadline specified",
                        "priority": priority,
                        "context": sentence_text,
                        "confidence": round(confidence, 2)
                    })
            
            logger.info(f"Found {len(action_items)} action items")
            priority_order = {"high": 0, "medium": 1, "low": 2}
            action_items.sort(key=lambda x: priority_order.get(x["priority"], 3))
            return action_items
        except Exception as e:
            logger.error(f"Action item extraction error: {str(e)}")
            raise
    
    def _contains_action_verb(self, text: str) -> bool:
        text_lower = text.lower()
        return any(verb in text_lower for verb in self.action_verbs)
    
    def _extract_assignee(self, sentence) -> Optional[str]:
        persons = [ent.text for ent in sentence.ents if ent.label_ == "PERSON"]
        if persons:
            return " and ".join(persons)
        roles = ["team", "designer", "developer", "manager", "lead", "engineer"]
        text_lower = sentence.text.lower()
        for role in roles:
            if f"the {role}" in text_lower:
                return f"The {role}"
        return None
    
    def _extract_deadline(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for pattern in self.date_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                return match.group(0).title()
        return None
    
    def _extract_priority(self, text: str) -> str:
        text_lower = text.lower()
        for keyword in self.priority_keywords["high"]:
            if keyword in text_lower:
                return "high"
        for keyword in self.priority_keywords["low"]:
            if keyword in text_lower:
                return "low"
        return "medium"
    
    def _extract_task_description(self, text: str) -> str:
        text = re.sub(r'^(so|well|um|uh|okay|alright),?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^(can you|could you|would you|will you)\s+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^[A-Z][a-z]+,\s*', '', text)
        text = text.strip()
        if text:
            text = text[0].upper() + text[1:]
        return text
    
    def _calculate_confidence(self, has_assignee, has_deadline, has_action_verb, sentence_length) -> float:
        score = 0.0
        if has_action_verb:
            score += 0.3
        if has_assignee:
            score += 0.3
        if has_deadline:
            score += 0.2
        if 5 <= sentence_length <= 30:
            score += 0.2
        return min(score, 1.0)