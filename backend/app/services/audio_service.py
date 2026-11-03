"""Audio processing service for speech-to-text transcription and audio summarization."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class AudioService:
    """Handles audio upload validation, Gemini-powered transcription, and summarization."""

    def __init__(self):
        self.allowed_extensions = set(settings.ALLOWED_AUDIO_EXTENSIONS)
        self.max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    def validate_audio(self, file: UploadFile) -> str:
        """Validate audio filename and extension, return MIME type."""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file has no filename.",
            )

        clean_filename = Path(file.filename).name
        ext = Path(clean_filename).suffix.lower()

        if ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported audio format '{ext}'. Allowed: {', '.join(sorted(self.allowed_extensions))}",
            )

        mime_map = {
            ".mp3": "audio/mp3",
            ".wav": "audio/wav",
            ".m4a": "audio/m4a",
            ".ogg": "audio/ogg",
            ".webm": "audio/webm",
            ".aac": "audio/aac",
        }
        return mime_map.get(ext, file.content_type or "audio/mp3")

    async def transcribe(self, audio_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """Transcribe speech in the audio file using Gemini audio capabilities."""
        if len(audio_bytes) > self.max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Audio file exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit.",
            )

        media_parts = [
            {
                "mime_type": mime_type,
                "data": audio_bytes,
            }
        ]

        prompt = (
            "Please transcribe the spoken audio verbatim in its original language. "
            "Output only the full, accurate text transcription without editorial commentary."
        )

        system_instruction = (
            "You are an expert audio transcription service. Provide clean, exact transcriptions "
            "with proper punctuation and paragraph breaks."
        )

        transcription = await gemini_service.generate_multimodal(
            prompt=prompt,
            media_parts=media_parts,
            system_instruction=system_instruction,
        )

        return {
            "transcription": transcription,
            "language": "auto",
            "model": settings.DEFAULT_MODEL,
        }

    async def summarize_audio(self, audio_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """Transcribe and generate structured executive summary, key points, and action items."""
        # First obtain the transcription
        trans_result = await self.transcribe(audio_bytes, mime_type)
        transcription = trans_result["transcription"]

        prompt = (
            f"AUDIO TRANSCRIPTION:\n\"\"\"{transcription}\"\"\"\n\n"
            "TASK:\n"
            "1. Write an Executive Summary of the audio content.\n"
            "2. Extract Key Points as bullet points.\n"
            "3. Extract Action Items or Next Steps if mentioned."
        )

        system_instruction = (
            "You are DARZFUSION AI's Audio Intelligence Assistant. "
            "Synthesize recorded conversations, meetings, and audio notes into actionable summaries."
        )

        summary_text = await gemini_service.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.3,
        )

        # Parse key points from summary
        key_points = []
        action_items = []
        for line in summary_text.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                key_points.append(line[2:])

        return {
            "transcription": transcription,
            "summary": summary_text,
            "key_points": key_points[:5],
            "action_items": action_items[:5],
            "model": settings.DEFAULT_MODEL,
        }


audio_service = AudioService()
