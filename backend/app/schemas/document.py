"""Document Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    name: str  # Frontend alias for original_filename
    original_filename: str
    file_type: str
    size: int  # in bytes
    page_count: int
    chunk_count: int
    status: str
    progress: int = 100
    uploadedAt: datetime  # Frontend alias
    created_at: datetime
    error_message: Optional[str] = None
    demo: bool = False

    class Config:
        from_attributes = True


class DocumentDeleteResponse(BaseModel):
    id: str
    deleted: bool = True
    message: str = "Document deleted successfully"
