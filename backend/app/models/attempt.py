import uuid
from datetime import datetime, timezone
from backend.app.extensions import db


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    quiz_id = db.Column(db.String(36), db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False, default=0)
    total_questions = db.Column(db.Integer, nullable=False, default=0)
    submitted_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = db.relationship("User", back_populates="attempts")
    quiz = db.relationship("Quiz", back_populates="attempts")
    answers = db.relationship("AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan", lazy="joined")

    def to_summary_dict(self) -> dict:
        percentage = round((self.score / self.total_questions) * 100, 2) if self.total_questions > 0 else 0.0
        return {
            "id": self.id,
            "quiz_id": self.quiz_id,
            "quiz_title": self.quiz.title if self.quiz else None,
            "score": self.score,
            "total_questions": self.total_questions,
            "accuracy_percentage": percentage,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
        }

    def to_results_dict(self) -> dict:
        """Full results returned only to the attempt owner after submission."""
        summary = self.to_summary_dict()
        summary["answers"] = [ans.to_dict() for ans in self.answers]
        return summary


class AttemptAnswer(db.Model):
    __tablename__ = "attempt_answers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attempt_id = db.Column(
        db.String(36),
        db.ForeignKey("quiz_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    question_id = db.Column(
        db.String(36),
        db.ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False
    )
    selected_option_id = db.Column(
        db.String(36),
        db.ForeignKey("question_options.id", ondelete="SET NULL"),
        nullable=True
    )
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    answered_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    attempt = db.relationship("QuizAttempt", back_populates="answers")
    question = db.relationship("Question")
    selected_option = db.relationship("QuestionOption", foreign_keys=[selected_option_id])

    def to_dict(self) -> dict:
        # Find correct option for this question
        correct_option = None
        if self.question and self.question.options:
            for opt in self.question.options:
                if opt.is_correct:
                    correct_option = {"id": opt.id, "option_text": opt.option_text}
                    break

        return {
            "id": self.id,
            "question_id": self.question_id,
            "question_prompt": self.question.prompt if self.question else None,
            "explanation": self.question.explanation if self.question else None,
            "selected_option_id": self.selected_option_id,
            "selected_option_text": self.selected_option.option_text if self.selected_option else None,
            "correct_option": correct_option,
            "is_correct": self.is_correct,
            "answered_at": self.answered_at.isoformat() if self.answered_at else None,
        }
