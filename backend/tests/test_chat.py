"""Tests for chat endpoints, model listing, and feedback."""

from unittest.mock import AsyncMock, patch


def test_list_models(client):
    """Verify list of available models."""
    response = client.get("/api/models")
    assert response.status_code == 200
    models = response.json()
    assert isinstance(models, list)
    assert len(models) >= 1
    assert any("gemini-2.5-flash" in m["id"] for m in models)


@patch("app.api.chat.gemini_service.chat", new_callable=AsyncMock)
def test_chat_single_message(mock_chat, client, auth_headers):
    """Test standard chat request."""
    mock_chat.return_value = "Retrieval-Augmented Generation combines retrieval with generative models."

    payload = {
        "message": "Explain retrieval-augmented generation",
        "conversation_id": None,
    }
    response = client.post("/api/chat", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "conversation_id" in data
    assert len(data["conversation_id"]) > 0
    assert "sources" in data
    assert data["answer"] == "Retrieval-Augmented Generation combines retrieval with generative models."


@patch("app.api.chat.gemini_service.chat", new_callable=AsyncMock)
def test_chat_empty_message_rejected(mock_chat, client):
    """Ensure blank messages are rejected with 400 Bad Request."""
    payload = {"message": "   "}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 400


def test_chat_feedback(client):
    """Test recording message feedback."""
    payload = {"messageId": "test-msg-id", "feedback": "up"}
    response = client.post("/api/chat/feedback", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
