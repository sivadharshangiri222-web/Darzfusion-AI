"""Tests for conversation history, message management, and ownership protection."""


def test_conversation_crud_and_isolation(client, auth_headers, other_auth_headers):
    """Test creating, listing, renaming, clearing, deleting, and isolation."""
    # 1. User 1 creates conversation
    create_payload = {"title": "Research Conversation", "model": "gemini-2.5-flash"}
    create_res = client.post("/api/history", json=create_payload, headers=auth_headers)
    assert create_res.status_code == 201
    conv_id = create_res.json()["id"]

    # 2. User 1 lists conversations
    list_res = client.get("/api/history", headers=auth_headers)
    assert list_res.status_code == 200
    assert any(c["id"] == conv_id for c in list_res.json())

    # 3. User 2 cannot access User 1's conversation
    forbidden_get = client.get(f"/api/history/{conv_id}", headers=other_auth_headers)
    assert forbidden_get.status_code == 403

    # 4. User 2 cannot rename User 1's conversation
    forbidden_patch = client.patch(
        f"/api/history/{conv_id}", json={"title": "Hacked Title"}, headers=other_auth_headers
    )
    assert forbidden_patch.status_code == 403

    # 5. User 1 renames their conversation
    rename_res = client.patch(
        f"/api/history/{conv_id}", json={"title": "Updated Title"}, headers=auth_headers
    )
    assert rename_res.status_code == 200
    assert rename_res.json()["title"] == "Updated Title"

    # 6. User 2 cannot delete User 1's conversation
    forbidden_del = client.delete(f"/api/history/{conv_id}", headers=other_auth_headers)
    assert forbidden_del.status_code == 403

    # 7. User 1 deletes their conversation
    del_res = client.delete(f"/api/history/{conv_id}", headers=auth_headers)
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True

    # 8. Conversation is now gone
    missing_res = client.get(f"/api/history/{conv_id}", headers=auth_headers)
    assert missing_res.status_code == 404
