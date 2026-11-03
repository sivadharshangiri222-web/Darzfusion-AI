"""AI Study Tools API endpoints: summarize, notes, quiz, flashcards, explain."""

from fastapi import APIRouter, HTTPException, status

from app.schemas.study import (
    ExplainRequest,
    ExplainResponse,
    FlashcardsRequest,
    FlashcardsResponse,
    NotesRequest,
    NotesResponse,
    QuizRequest,
    QuizResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from app.services.gemini_service import gemini_service
from app.services.study_service import study_service

router = APIRouter(prefix="/study", tags=["Study Tools"])


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_text(req: SummarizeRequest):
    """Summarize text with adjustable length."""
    if not req.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content cannot be empty.",
        )

    try:
        result = await study_service.summarize(text=req.text, length=req.length or "medium")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {str(e)}",
        )

    is_demo = not gemini_service.is_available()
    return SummarizeResponse(**result, demo=is_demo)


@router.post("/notes", response_model=NotesResponse)
async def generate_study_notes(req: NotesRequest):
    """Generate structured study notes formatted in Markdown."""
    if not req.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content cannot be empty.",
        )

    try:
        result = await study_service.generate_notes(text=req.text, title=req.title)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Notes generation failed: {str(e)}",
        )

    is_demo = not gemini_service.is_available()
    return NotesResponse(**result, demo=is_demo)


@router.post("/quiz", response_model=QuizResponse)
async def generate_quiz_endpoint(req: QuizRequest):
    """Generate multiple-choice quiz questions with answer keys."""
    if not req.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source material cannot be empty.",
        )

    try:
        result = await study_service.generate_quiz(
            text=req.text,
            question_count=req.question_count or 5,
            difficulty=req.difficulty or "medium",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz generation failed: {str(e)}",
        )

    is_demo = not gemini_service.is_available()
    return QuizResponse(**result, demo=is_demo)


@router.post("/flashcards", response_model=FlashcardsResponse)
async def generate_flashcards_endpoint(req: FlashcardsRequest):
    """Generate active recall flashcards (front/back/hint)."""
    if not req.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source material cannot be empty.",
        )

    try:
        result = await study_service.generate_flashcards(
            text=req.text,
            card_count=req.card_count or 6,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Flashcard generation failed: {str(e)}",
        )

    is_demo = not gemini_service.is_available()
    return FlashcardsResponse(**result, demo=is_demo)


@router.post("/explain", response_model=ExplainResponse)
async def explain_concept_endpoint(req: ExplainRequest):
    """Explain a complex concept simply with real-world analogies."""
    if not req.concept.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Concept cannot be empty.",
        )

    try:
        result = await study_service.explain_concept(
            concept=req.concept,
            level=req.level or "intermediate",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation failed: {str(e)}",
        )

    is_demo = not gemini_service.is_available()
    return ExplainResponse(**result, demo=is_demo)
