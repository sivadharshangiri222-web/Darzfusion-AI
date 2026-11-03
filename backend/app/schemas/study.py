"""Study tools schemas (summaries, notes, quizzes, flashcards, explain)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=10)
    length: Optional[str] = Field(default="medium", description="'short', 'medium', 'long'")


class SummarizeResponse(BaseModel):
    summary: str
    key_takeaways: List[str] = []
    word_count: int
    demo: bool = False


class NotesRequest(BaseModel):
    text: str = Field(..., min_length=10)
    title: Optional[str] = None


class NotesResponse(BaseModel):
    title: str
    notes_markdown: str
    key_concepts: List[str] = []
    summary: str
    demo: bool = False


class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str]
    correct_answer_index: int
    explanation: str


class QuizRequest(BaseModel):
    text: str = Field(..., min_length=10)
    question_count: Optional[int] = Field(default=5, ge=1, le=20)
    difficulty: Optional[str] = Field(default="medium", description="'easy', 'medium', 'hard'")


class QuizResponse(BaseModel):
    topic: str
    total_questions: int
    questions: List[QuizQuestion]
    demo: bool = False


class FlashcardItem(BaseModel):
    id: int
    front: str
    back: str
    hint: Optional[str] = None


class FlashcardsRequest(BaseModel):
    text: str = Field(..., min_length=10)
    card_count: Optional[int] = Field(default=6, ge=1, le=30)


class FlashcardsResponse(BaseModel):
    topic: str
    total_cards: int
    flashcards: List[FlashcardItem]
    demo: bool = False


class ExplainRequest(BaseModel):
    concept: str = Field(..., min_length=2)
    level: Optional[str] = Field(
        default="intermediate",
        description="'beginner', 'intermediate', 'advanced', 'child', 'expert'",
    )


class ExplainResponse(BaseModel):
    concept: str
    level: str
    explanation: str
    analogies: List[str] = []
    key_points: List[str] = []
    demo: bool = False
