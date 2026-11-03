"""Tests for RAG question answering and ChromaDB semantic retrieval."""

from unittest.mock import AsyncMock, patch


@patch("app.routers.rag.rag_service.answer_with_rag", new_callable=AsyncMock)
def test_rag_query_endpoint(mock_rag, client):
    """Test POST /api/rag/query with retrieved chunks and grounded answer."""
    mock_rag.return_value = {
        "answer": "According to the handbook, the refund window is 30 days.",
        "sources": [
            {
                "document_id": "doc-123",
                "document_name": "policy.pdf",
                "page": 3,
                "chunk_index": 1,
                "snippet": "Refunds are processed within 30 days of initial purchase.",
                "score": 0.94,
            }
        ],
        "has_sufficient_context": True,
        "query": "What is the refund window?",
    }

    payload = {
        "query": "What is the refund window?",
        "top_k": 4,
    }
    response = client.post("/api/rag/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["sources"]) == 1
    assert data["sources"][0]["document_name"] == "policy.pdf"
    assert data["sources"][0]["page"] == 3
    assert data["has_sufficient_context"] is True


def test_rag_empty_query_rejected(client):
    """Ensure empty query is rejected with 400 Bad Request."""
    payload = {"query": "   "}
    response = client.post("/api/rag/query", json=payload)
    assert response.status_code == 400
