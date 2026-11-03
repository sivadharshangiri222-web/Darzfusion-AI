"""Conversation history schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ConversationCreate(BaseModel):
    title: Optional[str] = "New conversation"
    model: Optional[str] = "gemini-2.5-flash"
    system_instruction: Optional[str] = None


class ConversationRename(BaseModel):
    title: str


class MessageItem(BaseModel):
    id: str
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    feedback: Optional[str] = None
    createdAt: datetime  # Frontend alias
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationSummary(BaseModel):
    id: str
    title: str
    model: str
    createdAt: datetime
    updatedAt: datetime
    created_at: datetime
    updated_at: datetime
    message_count: int

    class Config:
        from_attributes = True


class ConversationDetail(BaseModel):
    id: str
    title: str
    model: str
    system_instruction: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    created_at: datetime
    updated_at: datetime
    messages: List[MessageItem] = []

    class Config:
        from_attributes = True
