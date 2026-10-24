import uuid
from datetime import datetime, timezone
from backend.app.extensions import db


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = db.Column(db.String(36), db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    display_position = db.Column(db.Integer, nullable=False, default=0)
    topic = db.Column(db.String(100), nullable=True)
    difficulty = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    quiz = db.relationship("Quiz", back_populates="questions")
    options = db.relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan", lazy="joined")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "quiz_id": self.quiz_id,
            "prompt": self.prompt,
            "explanation": self.explanation,
            "display_position": self.display_position,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "options": [opt.to_dict() for opt in self.options],
        }

    def to_take_dict(self) -> dict:
        """Safe view for quiz taking: masks answers and explanations."""
        return {
            "id": self.id,
            "prompt": self.prompt,
            "display_position": self.display_position,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "options": [opt.to_take_dict() for opt in self.options],
        }
