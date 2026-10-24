
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


BASE_URL = "http://localhost:5000/api/v1"


class APIError(Exception):
    pass


def request(method, endpoint, data=None, token=None):
    headers = {"Accept": "application/json"}

    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(
        f"{BASE_URL}{endpoint}",
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urlopen(req, timeout=8) as response:
            content = response.read().decode("utf-8")
            return json.loads(content) if content else {}

    except HTTPError as exc:
        try:
            error_data = json.loads(exc.read().decode("utf-8"))
            message = error_data.get("error", {}).get(
                "message", f"Request failed ({exc.code})"
            )
        except (ValueError, AttributeError):
            message = f"Request failed ({exc.code})"
        raise APIError(message) from exc

    except URLError as exc:
        raise APIError(
            "Cannot connect to the FORMA backend. "
            "Make sure the backend is running on localhost:5000."
        ) from exc


def register(display_name, email, password):
    return request(
        "POST",
        "/auth/register",
        {
            "display_name": display_name,
            "email": email,
            "password": password,
        },
    )


def login(email, password):
    return request(
        "POST",
        "/auth/login",
        {
            "email": email,
            "password": password,
        },
    )


def get_quizzes(token):
    return request("GET", "/quizzes?include_public=true", token=token)

def create_quiz(title, description, questions, token, visibility="public"):
    return request(
        "POST",
        "/quizzes",
        {
            "title": title,
            "description": description,
            "visibility": visibility,
            "questions": questions,
        },
        token=token,
    )

def get_quiz(quiz_id, token):
    return request("GET", f"/quizzes/{quiz_id}", token=token)

def get_quiz_to_take(quiz_id, token):
    return request("GET", f"/quizzes/{quiz_id}/take", token=token)


def submit_attempt(quiz_id, answers, token):
    return request(
        "POST",
        f"/quizzes/{quiz_id}/attempts",
        {"answers": answers},
        token=token,
    )


def get_attempt_results(attempt_id, token):
    return request(
        "GET",
        f"/attempts/{attempt_id}/results",
        token=token,
    )