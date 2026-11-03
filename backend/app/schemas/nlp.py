"""NLP Toolkit schemas."""

from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field


class NLPRequest(BaseModel):
    tool: str = Field(
        ...,
        description="'summarize', 'keywords', 'ner', 'stats', 'preprocess'",
    )
    text: str = Field(..., min_length=1)
    options: Optional[Dict[str, Any]] = None


class NLPResponse(BaseModel):
    tool: str
    result: Union[str, Dict[str, Any], list]
    demo: bool = False
