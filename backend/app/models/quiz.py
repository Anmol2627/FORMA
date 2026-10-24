import uuid
from datetime import datetime, timezone
from backend.app.extensions import db


class Quiz(db.Model):
    __tablename__ = "quizzes"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    visibility = db.Column(db.String(20), nullable=False, default="private")  # "private" or "public"
    generation_metadata = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    owner = db.relationship("User", back_populates="quizzes")
    questions = db.relationship(
        "Question",
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="Question.display_position",
        lazy="joined"
    )
    attempts = db.relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self, include_questions: bool = True) -> dict:
        data = {
            "id": self.id,
            "owner_id": self.owner_id,
            "title": self.title,
            "description": self.description,
            "visibility": self.visibility,
            "generation_metadata": self.generation_metadata,
            "question_count": len(self.questions) if self.questions else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_questions:
            data["questions"] = [q.to_dict() for q in self.questions]
        return data

    def to_take_dict(self) -> dict:
        """Returns safe structure for taking quiz: NO answers, NO correctness, NO explanations."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "question_count": len(self.questions) if self.questions else 0,
            "questions": [q.to_take_dict() for q in self.questions],
        }
