"""Tests for Prompt Engineering Lab and NLP toolkit endpoints."""

from unittest.mock import AsyncMock, patch


def test_prompt_capabilities(client):
    """Verify prompt capabilities reporting."""
    response = client.get("/api/prompt/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["temperature"] is True
    assert data["maxTokens"] is True


@patch("app.api.prompt_lab.gemini_service.generate_text", new_callable=AsyncMock)
def test_prompt_run_zero_shot(mock_gen, client):
    """Test running zero shot prompt."""
    mock_gen.return_value = "Zero shot answer from model"

    payload = {
        "technique": "zero-shot",
        "prompt": "Explain gravity in one sentence",
        "temperature": 0.5,
    }
    response = client.post("/api/prompt/run", json=payload)
    assert response.status_code == 200
    assert response.json()["response"] == "Zero shot answer from model"
    assert response.json()["technique"] == "zero-shot"


def test_nlp_stats(client):
    """Test local text statistics calculation."""
    payload = {
        "tool": "stats",
        "text": "The quick brown fox jumps over the lazy dog. It was a sunny day.",
    }
    response = client.post("/api/nlp/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["tool"] == "stats"
    stats = data["result"]
    assert stats["word_count"] == 14
    assert stats["sentence_count"] == 2


def test_nlp_preprocess(client):
    """Test text preprocessing tool."""
    payload = {
        "tool": "preprocess",
        "text": "  Hello,    WORLD!   ",
        "options": {"lowercase": True, "remove_punctuation": True},
    }
    response = client.post("/api/nlp/run", json=payload)
    assert response.status_code == 200
    assert response.json()["result"] == "hello world"


def test_evaluation_endpoints(client):
    """Test evaluation benchmark run and history."""
    run_res = client.post("/api/evaluation/run")
    assert run_res.status_code == 200
    assert run_res.json()["status"] == "completed"

    hist_res = client.get("/api/evaluation/history")
    assert hist_res.status_code == 200
    assert isinstance(hist_res.json(), list)
    assert len(hist_res.json()) > 0
