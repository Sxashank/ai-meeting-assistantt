
# backend/services/summarization.py
# ==================================================

from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class SummarizationService:
    def __init__(self):
        model_name = "facebook/bart-large-cnn"
        logger.info(f"Loading summarization model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.summarizer = pipeline(
            "summarization",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if torch.cuda.is_available() else -1
        )
        logger.info("Summarization model loaded")
    
    async def summarize(self, text: str, max_length: int = 200) -> Dict:
        try:
            logger.info(f"Summarizing text of length: {len(text)}")
            max_chunk_length = 1024
            
            if len(text) > max_chunk_length:
                summary = await self._summarize_long_text(text, max_length)
            else:
                summary = self._summarize_chunk(text, max_length)
            
            return {
                "summary": summary,
                "original_length": len(text),
                "summary_length": len(summary),
                "compression_ratio": round(len(text) / len(summary), 2)
            }
        except Exception as e:
            logger.error(f"Summarization error: {str(e)}")
            raise
    
    def _summarize_chunk(self, text: str, max_length: int) -> str:
        result = self.summarizer(
            text,
            max_length=max_length,
            min_length=30,
            do_sample=False,
            truncation=True
        )
        return result[0]["summary_text"]
    
    async def _summarize_long_text(self, text: str, max_length: int) -> str:
        sentences = text.split('. ')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(self.tokenizer.encode(sentence))
            if current_length + sentence_length > 800:
                chunks.append('. '.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        if current_chunk:
            chunks.append('. '.join(current_chunk))
        
        logger.info(f"Split into {len(chunks)} chunks")
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Summarizing chunk {i+1}/{len(chunks)}")
            summary = self._summarize_chunk(chunk, max_length // len(chunks))
            chunk_summaries.append(summary)
        
        combined = ' '.join(chunk_summaries)
        final_summary = self._summarize_chunk(combined, max_length)
        return final_summary