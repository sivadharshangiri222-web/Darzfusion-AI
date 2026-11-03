"""Tests for document upload, processing, validation, and deletion."""

import io
from unittest.mock import AsyncMock, patch


@patch("app.routers.documents.rag_service.index_document_chunks", new_callable=AsyncMock)
def test_upload_txt_document(mock_index, client, auth_headers):
    """Test uploading and indexing a TXT document."""
    mock_index.return_value = 2

    file_content = b"DARZFUSION AI is an advanced multimodal generative AI platform. It supports documents, web search, and vision."
    files = {"file": ("darzfusion_intro.txt", io.BytesIO(file_content), "text/plain")}

    response = client.post("/api/documents/upload", files=files, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "darzfusion_intro.txt"
    assert data["file_type"] == "txt"
    assert data["status"] == "ready"
    assert data["chunk_count"] >= 1
    assert data["size"] == len(file_content)


def test_upload_invalid_extension(client, auth_headers):
    """Ensure disallowed file types are rejected with HTTP 400."""
    file_content = b"malicious executable or script"
    files = {"file": ("script.py", io.BytesIO(file_content), "text/x-python")}

    response = client.post("/api/documents/upload", files=files, headers=auth_headers)
    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()


@patch("app.routers.documents.rag_service.index_document_chunks", new_callable=AsyncMock)
def test_document_lifecycle_and_ownership(mock_index, client, auth_headers, other_auth_headers):
    """Test upload, retrieval, cross-user isolation, and deletion."""
    mock_index.return_value = 1

    # 1. User 1 uploads document
    files = {"file": ("private_notes.txt", io.BytesIO(b"Confidential user document content"), "text/plain")}
    upload_res = client.post("/api/documents/upload", files=files, headers=auth_headers)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # 2. User 1 can view document
    get_res = client.get(f"/api/documents/{doc_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == doc_id

    # 3. User 2 is forbidden from viewing User 1's document
    other_get_res = client.get(f"/api/documents/{doc_id}", headers=other_auth_headers)
    assert other_get_res.status_code == 403

    # 4. User 2 is forbidden from deleting User 1's document
    other_del_res = client.delete(f"/api/documents/{doc_id}", headers=other_auth_headers)
    assert other_del_res.status_code == 403

    # 5. User 1 can delete their own document
    del_res = client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True

    # 6. Document no longer exists
    missing_res = client.get(f"/api/documents/{doc_id}", headers=auth_headers)
    assert missing_res.status_code == 404
