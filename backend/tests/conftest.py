import shutil
import tempfile
import pytest
from backend.app import create_app
from backend.app.extensions import db
from backend.app.ai.llm_client import MockLLMClient


@pytest.fixture(scope="session")
def app():
    # Use temporary directory for uploads during tests
    temp_upload_dir = tempfile.mkdtemp(prefix="forma_test_uploads_")
    
    app = create_app("testing")
    app.config["UPLOAD_FOLDER"] = temp_upload_dir
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    
    # Inject MockLLMClient for AI tests
    app.llm_client = MockLLMClient()

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    # Clean up test uploads directory
    shutil.rmtree(temp_upload_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def client(app):
    with app.app_context():
        # Clear database between tests
        db.session.rollback()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Registers and logs in a primary user, returning valid Bearer auth headers."""
    register_payload = {
        "email": "primary@forma.dev",
        "password": "SecurePassword123!",
        "display_name": "Primary Student"
    }
    res = client.post("/api/v1/auth/register", json=register_payload)
    token = res.get_json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def other_user_headers(client):
    """Registers and logs in a secondary user for testing ownership and authorization barriers."""
    register_payload = {
        "email": "secondary@forma.dev",
        "password": "SecurePassword123!",
        "display_name": "Secondary Student"
    }
    res = client.post("/api/v1/auth/register", json=register_payload)
    token = res.get_json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
