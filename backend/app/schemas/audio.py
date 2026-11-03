"""Audio transcription and summarization schemas."""

from typing import List, Optional
from pydantic import BaseModel


class AudioTranscribeResponse(BaseModel):
    transcription: str
    language: Optional[str] = "en"
    duration_seconds: Optional[float] = None
    model: str = "gemini-2.5-flash"
    demo: bool = False


class AudioSummarizeResponse(BaseModel):
    transcription: str
    summary: str
    key_points: List[str] = []
    action_items: List[str] = []
    model: str = "gemini-2.5-flash"
    demo: bool = False
