"""Tests for vision and multimodal image analysis."""

import io
from unittest.mock import AsyncMock, patch


@patch("app.routers.vision.vision_service.analyze_image", new_callable=AsyncMock)
def test_vision_analyze(mock_analyze, client):
    """Test POST /api/vision/analyze with valid image."""
    mock_analyze.return_value = {
        "answer": "The image displays a modern architecture office building under a clear blue sky.",
        "description": "Architecture photography of high-rise glass building.",
        "detected_objects": ["building", "glass windows", "sky"],
        "model": "gemini-2.5-flash",
    }

    dummy_image = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    files = {"file": ("sample.png", io.BytesIO(dummy_image), "image/png")}
    data = {"question": "What is in this image?"}

    response = client.post("/api/vision/analyze", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert "office building" in res_data["answer"]


def test_vision_invalid_format(client):
    """Ensure unsupported image formats are rejected."""
    files = {"file": ("sample.pdf", io.BytesIO(b"not an image"), "application/pdf")}
    response = client.post("/api/vision/analyze", files=files)
    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()
