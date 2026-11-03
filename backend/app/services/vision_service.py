"""Vision service for multimodal image understanding and visual question answering."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class VisionService:
    """Processes image files and queries Gemini's multimodal capabilities."""

    def __init__(self):
        self.allowed_extensions = set(settings.ALLOWED_IMAGE_EXTENSIONS)
        self.max_size_bytes = 10 * 1024 * 1024  # 10 MB

    def validate_image(self, file: UploadFile) -> str:
        """Validate filename and format."""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file has no name.",
            )

        clean_filename = Path(file.filename).name
        ext = Path(clean_filename).suffix.lower()

        if ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported image format '{ext}'. Supported: {', '.join(sorted(self.allowed_extensions))}",
            )

        # Detect MIME type
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }
        return mime_map.get(ext, file.content_type or "image/jpeg")

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        question: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send image to Gemini multimodal model with the user's question."""
        if len(image_bytes) > self.max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image size exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit.",
            )

        prompt = question.strip() if (question and question.strip()) else (
            "Analyze this image in detail. Describe what is visible, "
            "identify any primary objects or persons, transcribe visible text if any, "
            "and note any unique or important visual characteristics."
        )

        media_parts = [
            {
                "mime_type": mime_type,
                "data": image_bytes,
            }
        ]

        system_instruction = (
            "You are DARZFUSION AI's Image Intelligence assistant. "
            "Examine the uploaded image with high fidelity and answer the user's inquiry accurately. "
            "Provide insightful, grounded visual descriptions without guessing."
        )

        answer = await gemini_service.generate_multimodal(
            prompt=prompt,
            media_parts=media_parts,
            system_instruction=system_instruction,
        )

        return {
            "answer": answer,
            "description": answer,
            "detected_objects": [],
            "model": settings.DEFAULT_MODEL,
        }


vision_service = VisionService()
