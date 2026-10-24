import threading
import time
from werkzeug.serving import make_server
import fitz  # PyMuPDF
import pytest

from desktop_app.services import api_client
from backend.app.ai.llm_client import MockLLMClient


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=5999):
        super().__init__()
        self.server = make_server(host, port, app)
        self.daemon = True

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


@pytest.fixture(scope="module")
def live_backend_server(app):
    app.llm_client = MockLLMClient()
    server = ServerThread(app, host="127.0.0.1", port=5999)
    server.start()
    time.sleep(0.5)

    original_base_url = api_client.get_base_url()
    api_client.set_base_url("http://127.0.0.1:5999/api/v1")

    yield "http://127.0.0.1:5999/api/v1"

    server.shutdown()
    api_client.set_base_url(original_base_url)


def test_full_e2e_workflow(live_backend_server, tmp_path):
    # 1. Register a new student
    reg = api_client.register("Alice Student", "alice@forma.edu", "StrongPass123!")
    token = reg["access_token"]
    assert token is not None
    assert reg["user"]["email"] == "alice@forma.edu"

    # 2. Login
    login_resp = api_client.login("alice@forma.edu", "StrongPass123!")
    assert login_resp["access_token"] is not None

    # 3. Get profile
    me = api_client.get_me(token)
    assert me["user"]["display_name"] == "Alice Student"

    # 4. Create a quiz
    questions = [
        {
            "prompt": "What does CPU stand for?",
            "explanation": "Central Processing Unit handles instructions.",
            "options": [
                {"option_text": "Central Processing Unit", "is_correct": True},
                {"option_text": "Central Power Unit", "is_correct": False},
                {"option_text": "Core Peripheral Unit", "is_correct": False},
                {"option_text": "Computer Process Unit", "is_correct": False},
            ]
        }
    ]
    created = api_client.create_quiz(
        title="Hardware 101",
        description="Intro to computing hardware",
        questions=questions,
        token=token,
        visibility="public"
    )
    quiz_id = created["quiz"]["id"]
    assert quiz_id is not None

    # 5. List accessible quizzes
    quizzes = api_client.get_quizzes(token, include_public=True)
    assert any(q["id"] == quiz_id for q in quizzes.get("quizzes", []))

    # 6. Get quiz to take (Security check: NO answer keys or explanations leaked)
    take_data = api_client.get_quiz_to_take(quiz_id, token)
    quiz_take = take_data["quiz"]
    assert len(quiz_take["questions"]) == 1
    q0 = quiz_take["questions"][0]
    assert "explanation" not in q0
    assert "is_correct" not in q0
    for opt in q0["options"]:
        assert "is_correct" not in opt

    # 7. Submit attempt
    correct_opt_id = None
    # Look up correct option from created quiz response for testing
    for opt in created["quiz"]["questions"][0]["options"]:
        if opt["is_correct"]:
            correct_opt_id = opt["id"]
            break

    submit_res = api_client.submit_attempt(
        quiz_id=quiz_id,
        answers=[{"question_id": q0["id"], "selected_option_id": correct_opt_id}],
        token=token
    )
    attempt_id = submit_res["attempt"]["id"]
    assert submit_res["attempt"]["score"] == 1
    assert submit_res["attempt"]["total_questions"] == 1
    assert submit_res["attempt"]["accuracy_percentage"] == 100.0

    # 8. Results review
    results_res = api_client.get_attempt_results(attempt_id, token)
    results = results_res["attempt"]
    assert results["score"] == 1
    assert results["answers"][0]["is_correct"] is True
    assert "Central Processing Unit" in results["answers"][0]["explanation"]

    # 9. AI Quiz Generation
    ai_gen = api_client.generate_ai_quiz("Operating Systems", token=token, question_count=1)
    ai_quiz = ai_gen.get("quiz", {})
    assert ai_quiz.get("id") is not None

    # 10. PDF Upload & Document Extraction
    pdf_path = tmp_path / "test_notes.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Operating Systems Concepts: Virtual Memory and Paging.")
    doc.save(str(pdf_path))
    doc.close()

    upload_res = api_client.upload_document(str(pdf_path), token)
    doc_id = upload_res["document"]["id"]
    assert upload_res["document"]["page_count"] == 1

    # 11. Chat Session & Message (RAG Pipeline returns grounded answer with citations)
    session_res = api_client.create_chat_session(doc_id, token, title="OS Study Session")
    session_id = session_res["session"]["id"]

    chat_resp = api_client.send_chat_message(session_id, "Explain virtual memory.", token)
    assert "assistant_message" in chat_resp
    assert chat_resp["assistant_message"]["content"]
    assert "user_message" in chat_resp

    # 12. Progress Analytics
    progress_res = api_client.get_progress(token)
    p = progress_res["progress"]
    assert p["total_attempts"] >= 1
    assert p["total_correct_answers"] >= 1
    assert p["overall_accuracy_percentage"] > 0
