"""Chat Pydantic schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str


class ChatAttachment(BaseModel):
    id: Optional[str] = None
    name: str
    type: str
    size: int
    url: Optional[str] = None


class ChatRequest(BaseModel):
    # Support both single message and conversation history
    message: Optional[str] = None
    conversation_id: Optional[str] = None
    conversationId: Optional[str] = None  # Frontend camelCase compatibility

    # Optional conversation context
    messages: Optional[List[ChatMessage]] = None
    attachments: Optional[List[Any]] = None

    # Model & Generation parameters
    model: Optional[str] = None
    system_instruction: Optional[str] = None
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=2048, ge=16, le=8192)

    # Retrieval and grounding toggles
    use_web_research: Optional[bool] = False
    use_documents: Optional[bool] = False
    useWebResearch: Optional[bool] = False
    useDocuments: Optional[bool] = False

    def get_message_content(self) -> str:
        """Extract user message from either message field or messages list."""
        if self.message and self.message.strip():
            return self.message.strip()
        if self.messages:
            for m in reversed(self.messages):
                if m.role == "user" and m.content.strip():
                    return m.content.strip()
        return ""

    def get_conversation_id(self) -> Optional[str]:
        return self.conversation_id or self.conversationId

    def get_use_web_research(self) -> bool:
        return bool(self.use_web_research or self.useWebResearch)

    def get_use_documents(self) -> bool:
        return bool(self.use_documents or self.useDocuments)


class ChatResponse(BaseModel):
    answer: str
    content: str  # For frontend compatibility
    conversation_id: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    model: str
    demo: bool = False
