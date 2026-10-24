from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from ..config import API_BASE_URL, API_TIMEOUT_SECONDS


class APIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details

    def __str__(self):
        return self.message


class ConnectionError(APIError):
    pass


class TimeoutError(APIError):
    pass


class AuthenticationError(APIError):
    pass


class ForbiddenError(APIError):
    pass


class NotFoundError(APIError):
    pass


class ValidationError(APIError):
    pass


class RAGNotImplementedError(APIError):
    pass


# Configurable base URL
_base_url = API_BASE_URL


def get_base_url() -> str:
    return _base_url


def set_base_url(url: str):
    global _base_url
    _base_url = url.rstrip("/")


def request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    url = f"{_base_url}{endpoint}"
    headers = {"Accept": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    effective_timeout = timeout if timeout is not None else API_TIMEOUT_SECONDS

    try:
        if files:
            # Multipart upload - requests will set proper Content-Type with boundary
            response = requests.request(
                method=method,
                url=url,
                params=params,
                data=data,
                files=files,
                headers=headers,
                timeout=effective_timeout,
            )
        else:
            if data is not None:
                headers["Content-Type"] = "application/json"
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=data if data is not None else None,
                headers=headers,
                timeout=effective_timeout,
            )

    except requests.exceptions.Timeout as exc:
        raise TimeoutError(
            f"The request to {endpoint} timed out after {effective_timeout}s. "
            "Please check your network and try again."
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise ConnectionError(
            "Cannot connect to the FORMA backend. "
            f"Please ensure the backend server is running at {_base_url}."
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise APIError(f"Network error while communicating with backend: {str(exc)}") from exc

    # Parse response content
    try:
        response_json = response.json() if response.content else {}
    except ValueError:
        response_json = None

    if response.ok:
        return response_json if response_json is not None else {}

    # Extract backend error schema: {"error": {"code": "...", "message": "...", "details": [...]}}
    status_code = response.status_code
    error_code = None
    message = f"Request failed with HTTP status {status_code}."
    details = None

    if isinstance(response_json, dict) and "error" in response_json:
        err_obj = response_json["error"]
        if isinstance(err_obj, dict):
            error_code = err_obj.get("code")
            message = err_obj.get("message", message)
            details = err_obj.get("details")
            # If validation error details are present, format a clean message
            if details and isinstance(details, list):
                field_msgs = [f"• {item.get('field', 'item')}: {item.get('message', '')}" for item in details if isinstance(item, dict)]
                if field_msgs:
                    message = f"{message}\n" + "\n".join(field_msgs)
        elif isinstance(err_obj, str):
            message = err_obj
    elif response.text:
        # Fallback to plain text snippet if not our standard JSON error
        snippet = response.text[:200].strip()
        if snippet:
            message = f"{message}: {snippet}"

    # Raise specific typed exceptions
    if status_code == 401:
        raise AuthenticationError(message, status_code=status_code, error_code=error_code, details=details)
    elif status_code == 403:
        raise ForbiddenError(message, status_code=status_code, error_code=error_code, details=details)
    elif status_code == 404:
        raise NotFoundError(message, status_code=status_code, error_code=error_code, details=details)
    elif status_code == 422:
        raise ValidationError(message, status_code=status_code, error_code=error_code, details=details)
    elif status_code == 501:
        raise RAGNotImplementedError(message, status_code=status_code, error_code=error_code, details=details)

    raise APIError(message, status_code=status_code, error_code=error_code, details=details)


# -------------------------------------------------------------------------
# Authentication Services
# -------------------------------------------------------------------------

def register(display_name: str, email: str, password: str) -> Dict[str, Any]:
    return request(
        "POST",
        "/auth/register",
        data={
            "display_name": display_name.strip(),
            "email": email.strip().lower(),
            "password": password,
        },
    )


def login(email: str, password: str) -> Dict[str, Any]:
    return request(
        "POST",
        "/auth/login",
        data={
            "email": email.strip().lower(),
            "password": password,
        },
    )


def get_me(token: str) -> Dict[str, Any]:
    return request("GET", "/auth/me", token=token)


# -------------------------------------------------------------------------
# Quiz Services
# -------------------------------------------------------------------------

def get_quizzes(token: str, include_public: bool = True) -> Dict[str, Any]:
    return request(
        "GET",
        "/quizzes",
        params={"include_public": "true" if include_public else "false"},
        token=token,
    )


def create_quiz(
    title: str,
    description: str,
    questions: List[Dict[str, Any]],
    token: str,
    visibility: str = "public",
) -> Dict[str, Any]:
    return request(
        "POST",
        "/quizzes",
        data={
            "title": title.strip(),
            "description": description.strip() if description else None,
            "visibility": visibility,
            "questions": questions,
        },
        token=token,
    )


def get_quiz(quiz_id: str, token: str) -> Dict[str, Any]:
    return request("GET", f"/quizzes/{quiz_id}", token=token)


def update_quiz(
    quiz_id: str,
    token: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    visibility: Optional[str] = None,
    questions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    if title is not None:
        payload["title"] = title
    if description is not None:
        payload["description"] = description
    if visibility is not None:
        payload["visibility"] = visibility
    if questions is not None:
        payload["questions"] = questions
    return request("PATCH", f"/quizzes/{quiz_id}", data=payload, token=token)


def delete_quiz(quiz_id: str, token: str) -> Dict[str, Any]:
    return request("DELETE", f"/quizzes/{quiz_id}", token=token)


def get_quiz_to_take(quiz_id: str, token: str) -> Dict[str, Any]:
    return request("GET", f"/quizzes/{quiz_id}/take", token=token)


# -------------------------------------------------------------------------
# Attempt & Scoring Services
# -------------------------------------------------------------------------

def submit_attempt(quiz_id: str, answers: List[Dict[str, Any]], token: str) -> Dict[str, Any]:
    return request(
        "POST",
        f"/quizzes/{quiz_id}/attempts",
        data={"answers": answers},
        token=token,
    )


def get_attempt_results(attempt_id: str, token: str) -> Dict[str, Any]:
    return request("GET", f"/attempts/{attempt_id}/results", token=token)


# -------------------------------------------------------------------------
# AI Quiz Generation Service
# -------------------------------------------------------------------------

def generate_ai_quiz(
    topic: str,
    token: str,
    question_count: int = 5,
    difficulty: str = "medium",
    source_text: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "topic": topic.strip(),
        "question_count": question_count,
        "difficulty": difficulty,
    }
    if source_text:
        payload["source_text"] = source_text.strip()
    return request("POST", "/ai/generate-quiz", data=payload, token=token, timeout=60)


# -------------------------------------------------------------------------
# Document & PDF Upload Services
# -------------------------------------------------------------------------

def upload_document(file_path: str, token: str) -> Dict[str, Any]:
    path = Path(file_path)
    if not path.is_file():
        raise APIError(f"File not found: {file_path}")

    with open(path, "rb") as f:
        files = {"file": (path.name, f, "application/pdf")}
        return request("POST", "/documents", files=files, token=token, timeout=30)


def get_documents(token: str) -> Dict[str, Any]:
    return request("GET", "/documents", token=token)


def get_document(document_id: str, token: str) -> Dict[str, Any]:
    return request("GET", f"/documents/{document_id}", token=token)


def delete_document(document_id: str, token: str) -> Dict[str, Any]:
    return request("DELETE", f"/documents/{document_id}", token=token)


# -------------------------------------------------------------------------
# Chat Session & Message Services (Ask Your PDF)
# -------------------------------------------------------------------------

def create_chat_session(document_id: str, token: str, title: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"document_id": document_id}
    if title:
        payload["title"] = title.strip()
    return request("POST", "/chat/sessions", data=payload, token=token)


def get_chat_sessions(token: str) -> Dict[str, Any]:
    return request("GET", "/chat/sessions", token=token)


def get_chat_messages(session_id: str, token: str) -> Dict[str, Any]:
    return request("GET", f"/chat/sessions/{session_id}/messages", token=token)


def send_chat_message(session_id: str, content: str, token: str) -> Dict[str, Any]:
    return request(
        "POST",
        f"/chat/sessions/{session_id}/messages",
        data={"content": content.strip()},
        token=token,
    )


# -------------------------------------------------------------------------
# Progress Analytics Services
# -------------------------------------------------------------------------

def get_progress(token: str) -> Dict[str, Any]:
    return request("GET", "/progress", token=token)