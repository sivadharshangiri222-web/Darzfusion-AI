"""Web search schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    depth: Optional[str] = Field(default="standard", description="'quick', 'standard', 'deep'")
    max_results: Optional[int] = Field(default=5, ge=1, le=15)


class SearchSource(BaseModel):
    title: str
    url: str
    snippet: str
    published_date: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    summary: str
    sources: List[SearchSource] = Field(default_factory=list)
    provider: str
    depth: str = "standard"
    demo: bool = False
