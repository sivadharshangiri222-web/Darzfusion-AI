"""Live Web Search API endpoints."""

from fastapi import APIRouter, HTTPException, status
from app.schemas.search import SearchRequest, SearchResponse, SearchSource
from app.services.gemini_service import gemini_service
from app.services.web_search_service import web_search_service

router = APIRouter(prefix="/search", tags=["Web Search"])


@router.post("", response_model=SearchResponse)
async def perform_search(req: SearchRequest):
    """Execute live web search, retrieve citations, and generate a grounded summary."""
    query = req.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty.",
        )

    try:
        result = await web_search_service.search_and_ground(
            query=query,
            depth=req.depth or "standard",
            max_results=req.max_results or 5,
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Web search failed: {str(e)}",
        )

    sources = [
        SearchSource(
            title=s["title"],
            url=s["url"],
            snippet=s["snippet"],
            published_date=s.get("published_date"),
        )
        for s in result.get("sources", [])
    ]

    is_demo = not gemini_service.is_available()

    return SearchResponse(
        query=result["query"],
        summary=result["summary"],
        sources=sources,
        provider=result["provider"],
        depth=result["depth"],
        demo=is_demo,
    )
