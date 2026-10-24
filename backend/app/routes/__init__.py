from backend.app.routes.health import health_bp
from backend.app.routes.auth import auth_bp
from backend.app.routes.quizzes import quizzes_bp
from backend.app.routes.attempts import attempts_bp
from backend.app.routes.ai import ai_bp
from backend.app.routes.documents import documents_bp
from backend.app.routes.chat import chat_bp
from backend.app.routes.progress import progress_bp

__all__ = [
    "health_bp",
    "auth_bp",
    "quizzes_bp",
    "attempts_bp",
    "ai_bp",
    "documents_bp",
    "chat_bp",
    "progress_bp",
]
