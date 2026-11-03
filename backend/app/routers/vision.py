"""Vision and Image Understanding API endpoints."""

from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.schemas.vision import VisionResponse
from app.services.gemini_service import gemini_service
from app.services.vision_service import vision_service

router = APIRouter(prefix="/vision", tags=["Vision"])


@router.post("/analyze", response_model=VisionResponse)
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    question: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None),
):
    """Analyze an uploaded image with Gemini multimodal understanding."""
    # Validate format and extract MIME type
    mime_type = vision_service.validate_image(file)

    # Read image bytes
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty.",
        )

    user_query = question or prompt

    try:
        result = await vision_service.analyze_image(
            image_bytes=image_bytes,
            mime_type=mime_type,
            question=user_query,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image analysis failed: {str(e)}",
        )

    is_demo = not gemini_service.is_available()

    return VisionResponse(
        answer=result["answer"],
        description=result.get("description"),
        detected_objects=result.get("detected_objects", []),
        model=result.get("model", "gemini-2.5-flash"),
        demo=is_demo,
    )
