from typing import List, Optional, Dict
from backend.app.extensions import db
from backend.app.models.attempt import QuizAttempt, AttemptAnswer


class AttemptRepository:
    @staticmethod
    def get_by_id(attempt_id: str) -> Optional[QuizAttempt]:
        return db.session.get(QuizAttempt, attempt_id)

    @staticmethod
    def list_by_user(user_id: str, limit: int = 50) -> List[QuizAttempt]:
        return (
            QuizAttempt.query.filter(QuizAttempt.user_id == user_id)
            .order_by(QuizAttempt.submitted_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def create_attempt_with_answers(
        user_id: str,
        quiz_id: str,
        total_questions: int,
        score: int,
        evaluated_answers: List[Dict]
    ) -> QuizAttempt:
        attempt = QuizAttempt(
            user_id=user_id,
            quiz_id=quiz_id,
            total_questions=total_questions,
            score=score
        )
        db.session.add(attempt)
        db.session.flush()

        for ans in evaluated_answers:
            attempt_answer = AttemptAnswer(
                attempt_id=attempt.id,
                question_id=ans["question_id"],
                selected_option_id=ans.get("selected_option_id"),
                is_correct=ans.get("is_correct", False)
            )
            db.session.add(attempt_answer)

        db.session.commit()
        return attempt

    @staticmethod
    def get_user_progress_stats(user_id: str) -> dict:
        attempts = QuizAttempt.query.filter(QuizAttempt.user_id == user_id).all()
        if not attempts:
            return {
                "total_attempts": 0,
                "total_questions_answered": 0,
                "total_correct_answers": 0,
                "overall_accuracy_percentage": 0.0,
                "recent_attempts": [],
            }

        total_attempts = len(attempts)
        total_questions = sum(a.total_questions for a in attempts)
        total_correct = sum(a.score for a in attempts)
        accuracy = round((total_correct / total_questions) * 100, 2) if total_questions > 0 else 0.0

        recent = (
            QuizAttempt.query.filter(QuizAttempt.user_id == user_id)
            .order_by(QuizAttempt.submitted_at.desc())
            .limit(10)
            .all()
        )

        return {
            "total_attempts": total_attempts,
            "total_questions_answered": total_questions,
            "total_correct_answers": total_correct,
            "overall_accuracy_percentage": accuracy,
            "recent_attempts": [a.to_summary_dict() for a in recent],
        }
