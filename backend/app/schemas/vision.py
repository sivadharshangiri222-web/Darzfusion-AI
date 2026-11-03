"""Vision and image understanding schemas."""

from typing import List, Optional
from pydantic import BaseModel


class VisionResponse(BaseModel):
    answer: str
    description: Optional[str] = None
    detected_objects: Optional[List[str]] = None
    extracted_text: Optional[str] = None
    model: str = "gemini-2.5-flash"
    demo: bool = False
