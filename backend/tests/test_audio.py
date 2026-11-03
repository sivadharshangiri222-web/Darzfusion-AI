"""Tests for audio transcription and summarization."""

import io
from unittest.mock import AsyncMock, patch


@patch("app.routers.audio.audio_service.transcribe", new_callable=AsyncMock)
def test_audio_transcribe(mock_transcribe, client):
    """Test POST /api/audio/transcribe."""
    mock_transcribe.return_value = {
        "transcription": "Welcome to DARZFUSION AI audio intelligence.",
        "language": "en",
        "duration_seconds": 3.5,
        "model": "gemini-2.5-flash",
    }

    dummy_audio = b"RIFF....WAVEfmt ...."
    files = {"file": ("speech.wav", io.BytesIO(dummy_audio), "audio/wav")}

    response = client.post("/api/audio/transcribe", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "DARZFUSION" in data["transcription"]


@patch("app.routers.audio.audio_service.summarize_audio", new_callable=AsyncMock)
def test_audio_summarize(mock_summarize, client):
    """Test POST /api/audio/summarize."""
    mock_summarize.return_value = {
        "transcription": "Meeting held regarding project release date and roadmap.",
        "summary": "The team agreed on releasing DARZFUSION AI backend this week.",
        "key_points": ["Backend completion", "Testing phase"],
        "action_items": ["Deploy on Render"],
        "model": "gemini-2.5-flash",
    }

    dummy_audio = b"ID3.....mp3data"
    files = {"file": ("meeting.mp3", io.BytesIO(dummy_audio), "audio/mp3")}

    response = client.post("/api/audio/summarize", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "releasing DARZFUSION" in data["summary"]
    assert len(data["key_points"]) >= 1


def test_audio_invalid_format(client):
    """Ensure invalid audio formats are rejected."""
    files = {"file": ("test.exe", io.BytesIO(b"binary"), "application/octet-stream")}
    response = client.post("/api/audio/transcribe", files=files)
    assert response.status_code == 400
