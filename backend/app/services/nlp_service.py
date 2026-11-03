"""NLP toolkit service for summarization, entity extraction, keywords, and text statistics."""

import re
from typing import Any, Dict, List, Optional, Union
from app.services.gemini_service import gemini_service


class NLPService:
    """Provides natural language processing utilities."""

    def calculate_stats(self, text: str) -> Dict[str, Any]:
        """Calculates text statistics locally without requiring external APIs."""
        words = text.split()
        word_count = len(words)
        char_count = len(text)
        char_count_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        sentence_count = len(sentences)
        avg_word_length = round(char_count_no_spaces / max(word_count, 1), 1)
        reading_time_minutes = round(word_count / 200, 1)  # standard ~200 wpm

        return {
            "word_count": word_count,
            "character_count": char_count,
            "character_count_no_spaces": char_count_no_spaces,
            "sentence_count": sentence_count,
            "average_word_length": avg_word_length,
            "estimated_reading_time_minutes": max(0.1, reading_time_minutes),
        }

    def preprocess_text(self, text: str, options: Dict[str, Any]) -> str:
        """Cleans and normalizes text according to user preferences."""
        cleaned = text
        if options.get("lowercase", False):
            cleaned = cleaned.lower()
        if options.get("remove_punctuation", False):
            cleaned = re.sub(r"[^\w\s]", "", cleaned)
        if options.get("remove_extra_whitespace", True):
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    async def run_tool(
        self, tool: str, text: str, options: Optional[Dict[str, Any]] = None
    ) -> Union[str, Dict[str, Any], List[Any]]:
        """Run requested NLP tool."""
        opts = options or {}

        if tool == "stats":
            return self.calculate_stats(text)

        if tool == "preprocess":
            return self.preprocess_text(text, opts)

        if tool == "keywords":
            top_k = opts.get("topK", 10)
            prompt = (
                f"TEXT:\n\"\"\"{text}\"\"\"\n\n"
                f"Extract the top {top_k} most important keywords, key phrases, and topics. "
                "Output as a comma-separated list."
            )
            response = await gemini_service.generate_text(
                prompt=prompt,
                system_instruction="You are an expert NLP keyword and keyphrase extraction system.",
                temperature=0.2,
            )
            keywords = [k.strip() for k in response.split(",") if k.strip()]
            return keywords[:top_k]

        if tool == "ner":
            prompt = (
                f"TEXT:\n\"\"\"{text}\"\"\"\n\n"
                "Extract Named Entities from this text categorized by: "
                "Persons, Organizations, Locations, and Dates/Events.\n"
                "Respond in clear Markdown format."
            )
            return await gemini_service.generate_text(
                prompt=prompt,
                system_instruction="You are a Named Entity Recognition (NER) extractor.",
                temperature=0.2,
            )

        if tool == "summarize":
            length = opts.get("length", "medium")
            prompt = (
                f"TEXT:\n\"\"\"{text}\"\"\"\n\n"
                f"Provide a {length} summary condensing the main ideas accurately."
            )
            return await gemini_service.generate_text(
                prompt=prompt,
                system_instruction="You are a concise text summarizer.",
                temperature=0.3,
            )

        raise ValueError(f"Unknown NLP tool: '{tool}'")


nlp_service = NLPService()
