"""Tests for application health and status endpoints."""


def test_health_check(client):
    """Verify root /health returns expected status and app name."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["application"] == "DARZFUSION AI"


def test_api_v1_health_check(client):
    """Verify /api/v1/health responds identically."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_services_status(client):
    """Verify /health/services reports sub-service health."""
    response = client.get("/health/services")
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert "gemini_api" in data["services"]
    assert "vector_store" in data["services"]
    assert "database" in data["services"]
