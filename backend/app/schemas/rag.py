"""Retrieval-Augmented Generation schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    query: Optional[str] = None
    question: Optional[str] = None  # Frontend alias
    document_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    top_k: int = Field(default=4, ge=1, le=20)

    def get_query(self) -> str:
        q = self.query or self.question
        return q.strip() if q else ""


class RAGSource(BaseModel):
    document_id: str
    document_name: str
    page: Optional[int] = None
    chunk_index: Optional[int] = None
    snippet: str
    score: Optional[float] = None


class RAGQueryResponse(BaseModel):
    answer: str
    query: str
    sources: List[RAGSource] = Field(default_factory=list)
    has_sufficient_context: bool = True
    model: str = "gemini-2.5-flash"
    demo: bool = False
