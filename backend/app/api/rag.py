"""RAG query and question answering API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user_optional
from app.models.user import User
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse, RAGSource
from app.services.gemini_service import gemini_service
from app.services.rag_service import rag_service

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/query", response_model=RAGQueryResponse)
@router.post("/ask", response_model=RAGQueryResponse)
async def query_rag(
    req: RAGQueryRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve relevant chunks and generate a context-grounded response using Gemini."""
    query_text = req.get_query()
    if not query_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty.",
        )

    user_id = current_user.id if current_user else None

    # Execute full RAG pipeline
    result = await rag_service.answer_with_rag(
        query=query_text,
        document_id=req.document_id,
        document_ids=req.document_ids,
        user_id=user_id,
        top_k=req.top_k,
    )

    sources = [
        RAGSource(
            document_id=s["document_id"],
            document_name=s["document_name"],
            page=s.get("page"),
            chunk_index=s.get("chunk_index"),
            snippet=s["snippet"],
            score=s.get("score"),
        )
        for s in result.get("sources", [])
    ]

    is_demo = not gemini_service.is_available()

    return RAGQueryResponse(
        answer=result["answer"],
        query=query_text,
        sources=sources,
        has_sufficient_context=result["has_sufficient_context"],
        demo=is_demo,
    )
