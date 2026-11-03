"""NLP Toolkit API endpoints."""

from fastapi import APIRouter, HTTPException, status
from app.schemas.nlp import NLPRequest, NLPResponse
from app.services.gemini_service import gemini_service
from app.services.nlp_service import nlp_service

router = APIRouter(prefix="/nlp", tags=["NLP Toolkit"])


@router.post("/run", response_model=NLPResponse)
async def run_nlp_tool(req: NLPRequest):
    """Run NLP utilities: summarization, keywords, NER, text stats, preprocessing."""
    if not req.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty.",
        )

    try:
        result = await nlp_service.run_tool(
            tool=req.tool,
            text=req.text,
            options=req.options or {},
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"NLP tool execution failed: {str(e)}",
        )

    is_demo = not gemini_service.is_available() and req.tool not in ["stats", "preprocess"]

    return NLPResponse(
        tool=req.tool,
        result=result,
        demo=is_demo,
    )
