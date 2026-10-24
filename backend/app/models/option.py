import uuid
from backend.app.extensions import db


class QuestionOption(db.Model):
    __tablename__ = "question_options"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = db.Column(
        db.String(36),
        db.ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    option_explanation = db.Column(db.Text, nullable=True)  # Why this option is correct/incorrect

    # Relationship
    question = db.relationship("Question", back_populates="options")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question_id": self.question_id,
            "option_text": self.option_text,
            "is_correct": self.is_correct,
            "option_explanation": self.option_explanation,
        }

    def to_take_dict(self) -> dict:
        """Safe option structure for student during test: option_id and text only."""
        return {
            "id": self.id,
            "option_text": self.option_text,
        }

