"""Prompt Engineering Lab schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PromptLabExample(BaseModel):
    input: str
    output: str


class PromptLabRequest(BaseModel):
    technique: str = Field(
        ...,
        description="'zero-shot', 'few-shot', 'role', 'structured', 'step-by-step'",
    )
    user: Optional[str] = None
    prompt: Optional[str] = None
    system: Optional[str] = None
    role: Optional[str] = None
    examples: Optional[List[PromptLabExample]] = None
    output_format: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

    def get_user_prompt(self) -> str:
        return (self.user or self.prompt or "").strip()


class PromptCapabilitiesResponse(BaseModel):
    temperature: bool = True
    maxTokens: bool = True


class PromptLabResponse(BaseModel):
    response: str
    technique: str
    model: str = "gemini-2.5-flash"
    demo: bool = False
