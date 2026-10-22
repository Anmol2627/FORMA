
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
