from unittest.mock import MagicMock, patch
import pytest

from desktop_app.services import api_client


def test_api_client_register_success():
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 201
    mock_resp.content = b'{"user": {"id": "u1", "email": "test@forma.dev", "display_name": "Test User"}, "access_token": "jwt-tok"}'
    mock_resp.json.return_value = {
        "user": {"id": "u1", "email": "test@forma.dev", "display_name": "Test User"},
        "access_token": "jwt-tok"
    }

    with patch("requests.request", return_value=mock_resp) as mock_req:
        res = api_client.register("Test User", "test@forma.dev", "Password123!")
        assert res["access_token"] == "jwt-tok"
        assert res["user"]["email"] == "test@forma.dev"
        mock_req.assert_called_once()
        args, kwargs = mock_req.call_args
        assert kwargs["json"]["email"] == "test@forma.dev"


def test_api_client_auth_error_401():
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 401
    mock_resp.json.return_value = {
        "error": {"code": "invalid_credentials", "message": "Invalid email or password"}
    }

    with patch("requests.request", return_value=mock_resp):
        with pytest.raises(api_client.AuthenticationError) as exc_info:
            api_client.login("user@forma.dev", "wrong-pwd")
        assert "Invalid email or password" in str(exc_info.value)
        assert exc_info.value.status_code == 401


def test_api_client_validation_error_422():
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 422
    mock_resp.json.return_value = {
        "error": {
            "code": "validation_error",
            "message": "Input validation failed",
            "details": [{"field": "body.password", "message": "Password must be at least 8 characters long"}]
        }
    }

    with patch("requests.request", return_value=mock_resp):
        with pytest.raises(api_client.ValidationError) as exc_info:
            api_client.register("User", "user@forma.dev", "short")
        assert "Password must be at least 8 characters long" in str(exc_info.value)
        assert exc_info.value.status_code == 422


def test_api_client_rag_not_implemented_501():
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 501
    mock_resp.json.return_value = {
        "error": {
            "code": "rag_pipeline_not_implemented",
            "message": "The RAG retrieval pipeline is currently awaiting implementation."
        }
    }

    with patch("requests.request", return_value=mock_resp):
        with pytest.raises(api_client.RAGNotImplementedError) as exc_info:
            api_client.send_chat_message("session-1", "What is mitochondria?", token="tok")
        assert "RAG retrieval pipeline is currently awaiting implementation" in str(exc_info.value)
        assert exc_info.value.status_code == 501


def test_api_client_quiz_lifecycle():
    # 1. Create quiz
    create_resp = MagicMock(ok=True, status_code=201, content=b'{"quiz": {"id": "q1", "title": "Math 101"}}')
    create_resp.json.return_value = {"quiz": {"id": "q1", "title": "Math 101"}}

    # 2. Get quiz to take
    take_resp = MagicMock(ok=True, status_code=200, content=b'{"quiz": {"id": "q1", "title": "Math 101", "questions": []}}')
    take_resp.json.return_value = {"quiz": {"id": "q1", "title": "Math 101", "questions": []}}

    # 3. Submit attempt
    submit_resp = MagicMock(ok=True, status_code=201, content=b'{"attempt": {"id": "a1", "score": 1, "total_questions": 1}}')
    submit_resp.json.return_value = {"attempt": {"id": "a1", "score": 1, "total_questions": 1}}

    # 4. Results
    results_resp = MagicMock(ok=True, status_code=200, content=b'{"attempt": {"id": "a1", "score": 1, "answers": []}}')
    results_resp.json.return_value = {"attempt": {"id": "a1", "score": 1, "answers": []}}

    with patch("requests.request", side_effect=[create_resp, take_resp, submit_resp, results_resp]):
        created = api_client.create_quiz("Math 101", "Basic math", [], token="tok")
        assert created["quiz"]["id"] == "q1"

        taken = api_client.get_quiz_to_take("q1", token="tok")
        assert taken["quiz"]["id"] == "q1"

        submitted = api_client.submit_attempt("q1", [{"question_id": "q_id", "selected_option_id": "opt_1"}], token="tok")
        assert submitted["attempt"]["id"] == "a1"

        reviewed = api_client.get_attempt_results("a1", token="tok")
        assert reviewed["attempt"]["id"] == "a1"


def test_api_client_progress():
    progress_resp = MagicMock(
        ok=True,
        status_code=200,
        content=b'{"progress": {"total_attempts": 2, "total_questions_answered": 10, "total_correct_answers": 8, "overall_accuracy_percentage": 80.0, "recent_attempts": []}}'
    )
    progress_resp.json.return_value = {
        "progress": {
            "total_attempts": 2,
            "total_questions_answered": 10,
            "total_correct_answers": 8,
            "overall_accuracy_percentage": 80.0,
            "recent_attempts": []
        }
    }

    with patch("requests.request", return_value=progress_resp):
        p = api_client.get_progress("tok")
        assert p["progress"]["total_attempts"] == 2
        assert p["progress"]["overall_accuracy_percentage"] == 80.0


def test_api_client_connection_error():
    import requests

    with patch("requests.request", side_effect=requests.exceptions.ConnectionError("Connection refused")):
        with pytest.raises(api_client.ConnectionError) as exc_info:
            api_client.get_quizzes("tok")
        assert "Cannot connect to the FORMA backend" in str(exc_info.value)
