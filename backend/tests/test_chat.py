import io
from backend.tests.test_documents import create_sample_pdf_bytes


def setup_test_document(client, auth_headers):
    pdf_bytes = create_sample_pdf_bytes()
    res = client.post(
        "/api/v1/documents",
        data={"file": (io.BytesIO(pdf_bytes), "lecture_notes.pdf")},
        content_type="multipart/form-data",
        headers={"Authorization": auth_headers["Authorization"]}
    )
    return res.get_json()["document"]["id"]


def test_chat_session_creation_and_listing(client, auth_headers, other_user_headers):
    doc_id = setup_test_document(client, auth_headers)

    # Primary user creates session
    res = client.post(
        "/api/v1/chat/sessions",
        json={"document_id": doc_id, "title": "Midterm Prep"},
        headers=auth_headers
    )
    assert res.status_code == 201
    session = res.get_json()["session"]
    assert session["title"] == "Midterm Prep"
    assert session["document_id"] == doc_id
    session_id = session["id"]

    # Secondary user attempts to create session for primary user's document -> 403 Forbidden
    res_forbidden = client.post(
        "/api/v1/chat/sessions",
        json={"document_id": doc_id, "title": "Unauthorized Prep"},
        headers=other_user_headers
    )
    assert res_forbidden.status_code == 403

    # Primary user lists sessions
    list_res = client.get("/api/v1/chat/sessions", headers=auth_headers)
    assert list_res.status_code == 200
    sessions = list_res.get_json()["sessions"]
    assert any(s["id"] == session_id for s in sessions)


def test_chat_messages_rag_not_implemented_response(client, auth_headers, other_user_headers):
    doc_id = setup_test_document(client, auth_headers)
    session_res = client.post(
        "/api/v1/chat/sessions",
        json={"document_id": doc_id, "title": "Q&A Session"},
        headers=auth_headers
    )
    session_id = session_res.get_json()["session"]["id"]

    # Post message -> Validates input, saves user query, returns 501 Not Implemented
    msg_res = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "What is covered on page 1?"},
        headers=auth_headers
    )
    assert msg_res.status_code == 501
    err_data = msg_res.get_json()["error"]
    assert err_data["code"] == "rag_pipeline_not_implemented"
    assert "docs/RAG_INTEGRATION.md" in err_data["message"]

    # Verify user message was persisted in history despite 501 RAG status
    history_res = client.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=auth_headers)
    assert history_res.status_code == 200
    messages = history_res.get_json()["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "What is covered on page 1?"

    # Other user attempts to access message history -> 403 Forbidden
    forbidden_history = client.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=other_user_headers)
    assert forbidden_history.status_code == 403


def test_chat_message_validation(client, auth_headers):
    doc_id = setup_test_document(client, auth_headers)
    session_res = client.post(
        "/api/v1/chat/sessions",
        json={"document_id": doc_id},
        headers=auth_headers
    )
    session_id = session_res.get_json()["session"]["id"]

    # Blank message content
    res = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "   "},
        headers=auth_headers
    )
    assert res.status_code == 422
