"""Audio processing API endpoints: transcription and summarization."""

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.audio import AudioSummarizeResponse, AudioTranscribeResponse
from app.services.audio_service import audio_service
from app.services.gemini_service import gemini_service

router = APIRouter(prefix="/audio", tags=["Audio"])


@router.post("/transcribe", response_model=AudioTranscribeResponse)
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    """Transcribe speech in an audio file using Gemini audio capabilities."""
    mime_type = audio_service.validate_audio(file)

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file is empty.",
        )

    try:
        result = await audio_service.transcribe(audio_bytes, mime_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio transcription failed: {str(e)}",
        )

    is_demo = not gemini_service.is_available()

    return AudioTranscribeResponse(
        transcription=result["transcription"],
        language=result.get("language", "auto"),
        duration_seconds=result.get("duration_seconds"),
        model=result.get("model", "gemini-2.5-flash"),
        demo=is_demo,
    )


@router.post("/summarize", response_model=AudioSummarizeResponse)
async def summarize_audio_endpoint(file: UploadFile = File(...)):
    """Transcribe audio and generate an executive summary with key takeaways."""
    mime_type = audio_service.validate_audio(file)

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file is empty.",
        )

    try:
        result = await audio_service.summarize_audio(audio_bytes, mime_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio summarization failed: {str(e)}",
        )

    is_demo = not gemini_service.is_available()

    return AudioSummarizeResponse(
        transcription=result["transcription"],
        summary=result["summary"],
        key_points=result.get("key_points", []),
        action_items=result.get("action_items", []),
        model=result.get("model", "gemini-2.5-flash"),
        demo=is_demo,
    )
