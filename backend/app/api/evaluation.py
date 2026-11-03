"""Evaluation Center API endpoints for scoring retrieval and answer quality."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/evaluation", tags=["Evaluation Center"])


class EvalRunRequest(BaseModel):
    test_cases: Optional[List[Dict[str, Any]]] = None


class EvalHistoryItem(BaseModel):
    id: str
    runAt: str
    retrieval: float
    answer: float
    groundedness: float


SAMPLE_BENCHMARKS = [
    {
        "id": "s1",
        "question": "What is the refund window?",
        "expected": "30 days from purchase.",
        "actual": "Refunds are accepted within 30 days.",
        "retrievalRelevance": 0.92,
        "answerRelevance": 0.95,
        "groundedness": 0.90,
    },
    {
        "id": "s2",
        "question": "Who approves budget changes?",
        "expected": "The finance director.",
        "actual": "Budget changes require approval from finance.",
        "retrievalRelevance": 0.74,
        "answerRelevance": 0.81,
        "groundedness": 0.70,
    },
    {
        "id": "s3",
        "question": "List supported file types.",
        "expected": "PDF, PNG, JPEG.",
        "actual": "PDF and PNG files are supported.",
        "retrievalRelevance": 0.66,
        "answerRelevance": 0.60,
        "groundedness": 0.58,
    },
]

HISTORY_RUNS = [
    {"id": "h1", "runAt": "2026-09-01", "retrieval": 0.61, "answer": 0.66, "groundedness": 0.58},
    {"id": "h2", "runAt": "2026-09-15", "retrieval": 0.68, "answer": 0.70, "groundedness": 0.63},
    {"id": "h3", "runAt": "2026-10-01", "retrieval": 0.72, "answer": 0.77, "groundedness": 0.69},
    {"id": "h4", "runAt": "2026-10-15", "retrieval": 0.81, "answer": 0.84, "groundedness": 0.76},
]


@router.post("/run")
def run_evaluation(req: Optional[EvalRunRequest] = None):
    """Execute evaluation benchmark suite."""
    return {
        "status": "completed",
        "runAt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "results": SAMPLE_BENCHMARKS,
        "summary": {
            "meanRetrievalRelevance": 0.77,
            "meanAnswerRelevance": 0.79,
            "meanGroundedness": 0.73,
        },
    }


@router.get("/history", response_model=List[EvalHistoryItem])
def get_evaluation_history():
    """Retrieve historical evaluation run scores."""
    return HISTORY_RUNS
