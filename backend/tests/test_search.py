"""Tests for live web search and source grounding."""

from unittest.mock import AsyncMock, patch


@patch("app.api.search.web_search_service.search_and_ground", new_callable=AsyncMock)
def test_search_endpoint(mock_search, client):
    """Test POST /api/search."""
    mock_search.return_value = {
        "query": "FastAPI async",
        "summary": "FastAPI is designed for high concurrency with asynchronous Python.",
        "sources": [
            {
                "title": "FastAPI Documentation",
                "url": "https://fastapi.tiangolo.com",
                "snippet": "FastAPI framework, high performance, easy to learn.",
                "published_date": "2026-01-01",
            }
        ],
        "provider": "duckduckgo",
        "depth": "standard",
    }

    payload = {"query": "FastAPI async", "depth": "standard"}
    response = client.post("/api/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "FastAPI async"
    assert "FastAPI" in data["summary"]
    assert len(data["sources"]) == 1
    assert data["sources"][0]["url"] == "https://fastapi.tiangolo.com"


def test_search_empty_query_rejected(client):
    """Ensure empty search query is rejected with 400 Bad Request."""
    payload = {"query": " "}
    response = client.post("/api/search", json=payload)
    assert response.status_code == 422 or response.status_code == 400
