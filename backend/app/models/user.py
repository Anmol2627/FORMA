import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from backend.app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    account_status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    quizzes = db.relationship("Quiz", back_populates="owner", cascade="all, delete-orphan", lazy="dynamic")
    attempts = db.relationship("QuizAttempt", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    documents = db.relationship("Document", back_populates="owner", cascade="all, delete-orphan", lazy="dynamic")
    chat_sessions = db.relationship("ChatSession", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "display_name": self.display_name,
            "account_status": self.account_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
