def test_register_success(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "student1@example.com",
        "password": "StrongPassword123!",
        "display_name": "Alice"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert "access_token" in data
    assert data["user"]["email"] == "student1@example.com"
    assert data["user"]["display_name"] == "Alice"
    assert "password_hash" not in data["user"]


def test_register_duplicate_email(client):
    payload = {
        "email": "duplicate@example.com",
        "password": "StrongPassword123!",
        "display_name": "Bob"
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    data = res2.get_json()
    assert data["error"]["code"] == "user_already_exists"


def test_register_invalid_inputs(client):
    # Short password
    res = client.post("/api/v1/auth/register", json={
        "email": "invalid@example.com",
        "password": "short",
        "display_name": "Carol"
    })
    assert res.status_code == 422
    assert res.get_json()["error"]["code"] == "validation_error"

    # Invalid email format
    res = client.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "password": "ValidPassword123!",
        "display_name": "Carol"
    })
    assert res.status_code == 422

    # Blank display name
    res = client.post("/api/v1/auth/register", json={
        "email": "carol@example.com",
        "password": "ValidPassword123!",
        "display_name": "   "
    })
    assert res.status_code == 422


def test_login_success(client):
    client.post("/api/v1/auth/register", json={
        "email": "login_user@example.com",
        "password": "SecretPassword123!",
        "display_name": "Dave"
    })

    res = client.post("/api/v1/auth/login", json={
        "email": "login_user@example.com",
        "password": "SecretPassword123!"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "access_token" in data
    assert data["user"]["email"] == "login_user@example.com"


def test_login_incorrect_credentials(client):
    client.post("/api/v1/auth/register", json={
        "email": "user@example.com",
        "password": "CorrectPassword123!",
        "display_name": "Dave"
    })

    # Wrong password
    res = client.post("/api/v1/auth/login", json={
        "email": "user@example.com",
        "password": "WrongPassword123!"
    })
    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "invalid_credentials"

    # Non-existent email
    res2 = client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "Password123!"
    })
    assert res2.status_code == 401


def test_protected_routes_unauthorized(client):
    # Without token
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "unauthorized"

    # With invalid token
    res2 = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-valid-token"})
    assert res2.status_code == 401
    assert res2.get_json()["error"]["code"] == "invalid_token"


def test_auth_me_success(client, auth_headers):
    res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["user"]["email"] == "primary@forma.dev"
    assert data["user"]["display_name"] == "Primary Student"
