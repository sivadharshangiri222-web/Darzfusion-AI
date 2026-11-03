"""Tests for AI study tools (summarize, notes, quiz, flashcards, explain)."""

from unittest.mock import AsyncMock, patch


@patch("app.api.study_tools.study_service.summarize", new_callable=AsyncMock)
def test_summarize(mock_sum, client):
    """Test text summarization endpoint."""
    mock_sum.return_value = {
        "summary": "Photosynthesis is the biological process converting light into chemical energy.",
        "key_takeaways": ["Requires sunlight and CO2", "Produces glucose and oxygen"],
        "word_count": 25,
    }

    payload = {"text": "Photosynthesis is the process by which green plants and certain organisms transform light energy into chemical energy.", "length": "short"}
    response = client.post("/api/study/summarize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Photosynthesis" in data["summary"]
    assert len(data["key_takeaways"]) == 2


@patch("app.api.study_tools.study_service.generate_notes", new_callable=AsyncMock)
def test_notes(mock_notes, client):
    """Test notes generation endpoint."""
    mock_notes.return_value = {
        "title": "Machine Learning Fundamentals",
        "notes_markdown": "# Machine Learning\n\n- Supervised Learning\n- Unsupervised Learning",
        "key_concepts": ["Supervised", "Unsupervised"],
        "summary": "Foundational ML paradigms",
    }

    payload = {"text": "Machine learning comprises supervised, unsupervised, and reinforcement learning methods.", "title": "Machine Learning Fundamentals"}
    response = client.post("/api/study/notes", json=payload)
    assert response.status_code == 200
    assert "Machine Learning" in response.json()["notes_markdown"]


@patch("app.api.study_tools.study_service.generate_quiz", new_callable=AsyncMock)
def test_quiz(mock_quiz, client):
    """Test multiple-choice quiz generation with answer keys."""
    mock_quiz.return_value = {
        "topic": "Python Generators",
        "total_questions": 1,
        "questions": [
            {
                "id": 1,
                "question": "Which keyword is used to yield values lazily in Python?",
                "options": ["yield", "return", "pass", "def"],
                "correct_answer_index": 0,
                "explanation": "'yield' produces generator values iteratively.",
            }
        ],
    }

    payload = {"text": "Python generators produce items lazily using the yield statement.", "question_count": 1}
    response = client.post("/api/study/quiz", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_questions"] == 1
    assert data["questions"][0]["options"][0] == "yield"


@patch("app.api.study_tools.study_service.generate_flashcards", new_callable=AsyncMock)
def test_flashcards(mock_fc, client):
    """Test flashcard deck generation."""
    mock_fc.return_value = {
        "topic": "Databases",
        "total_cards": 1,
        "flashcards": [
            {
                "id": 1,
                "front": "What does ACID stand for?",
                "back": "Atomicity, Consistency, Isolation, Durability",
                "hint": "Database transaction properties",
            }
        ],
    }

    payload = {"text": "ACID properties ensure reliable database transaction processing."}
    response = client.post("/api/study/flashcards", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["flashcards"]) == 1
    assert "Atomicity" in data["flashcards"][0]["back"]


@patch("app.api.study_tools.study_service.explain_concept", new_callable=AsyncMock)
def test_explain(mock_explain, client):
    """Test concept explainer endpoint."""
    mock_explain.return_value = {
        "concept": "Neural Networks",
        "level": "beginner",
        "explanation": "A neural network is like a team of layered detectives solving a mystery.",
        "analogies": ["Layered detectives"],
        "key_points": ["Weights", "Biases"],
    }

    payload = {"concept": "Neural Networks", "level": "beginner"}
    response = client.post("/api/study/explain", json=payload)
    assert response.status_code == 200
    assert "detectives" in response.json()["explanation"]
