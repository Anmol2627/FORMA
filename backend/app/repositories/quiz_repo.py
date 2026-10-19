from typing import List, Optional
from sqlalchemy import or_
from backend.app.extensions import db
from backend.app.models.quiz import Quiz
from backend.app.models.question import Question
from backend.app.models.option import QuestionOption


class QuizRepository:
    @staticmethod
    def get_by_id(quiz_id: str) -> Optional[Quiz]:
        return db.session.get(Quiz, quiz_id)

    @staticmethod
    def list_accessible(user_id: str, include_public: bool = True) -> List[Quiz]:
        """Returns quizzes owned by the user, plus any public quizzes if include_public is True."""
        query = Quiz.query
        if include_public:
            query = query.filter(or_(Quiz.owner_id == user_id, Quiz.visibility == "public"))
        else:
            query = query.filter(Quiz.owner_id == user_id)
        return query.order_by(Quiz.created_at.desc()).all()

    @staticmethod
    def create(
        owner_id: str,
        title: str,
        description: Optional[str] = None,
        visibility: str = "private",
        generation_metadata: Optional[dict] = None,
        questions_data: Optional[List[dict]] = None
    ) -> Quiz:
        quiz = Quiz(
            owner_id=owner_id,
            title=title.strip(),
            description=description.strip() if description else None,
            visibility=visibility,
            generation_metadata=generation_metadata
        )
        db.session.add(quiz)
        db.session.flush()

        if questions_data:
            for idx, q_data in enumerate(questions_data):
                question = Question(
                    quiz_id=quiz.id,
                    prompt=q_data["prompt"].strip(),
                    explanation=q_data.get("explanation"),
                    display_position=q_data.get("display_position", idx),
                    topic=q_data.get("topic"),
                    difficulty=q_data.get("difficulty", "medium")
                )
                db.session.add(question)
                db.session.flush()

                for opt_data in q_data.get("options", []):
                    option = QuestionOption(
                        question_id=question.id,
                        option_text=opt_data["option_text"].strip(),
                        is_correct=bool(opt_data.get("is_correct", False))
                    )
                    db.session.add(option)

        db.session.commit()
        return quiz

    @staticmethod
    def update(
        quiz: Quiz,
        title: Optional[str] = None,
        description: Optional[str] = None,
        visibility: Optional[str] = None,
        questions_data: Optional[List[dict]] = None
    ) -> Quiz:
        if title is not None:
            quiz.title = title.strip()
        if description is not None:
            quiz.description = description.strip() if description else None
        if visibility is not None:
            quiz.visibility = visibility

        if questions_data is not None:
            # Replace questions safely
            for existing_q in list(quiz.questions):
                db.session.delete(existing_q)
            db.session.flush()

            for idx, q_data in enumerate(questions_data):
                question = Question(
                    quiz_id=quiz.id,
                    prompt=q_data["prompt"].strip(),
                    explanation=q_data.get("explanation"),
                    display_position=q_data.get("display_position", idx),
                    topic=q_data.get("topic"),
                    difficulty=q_data.get("difficulty", "medium")
                )
                db.session.add(question)
                db.session.flush()

                for opt_data in q_data.get("options", []):
                    option = QuestionOption(
                        question_id=question.id,
                        option_text=opt_data["option_text"].strip(),
                        is_correct=bool(opt_data.get("is_correct", False))
                    )
                    db.session.add(option)

        db.session.commit()
        return quiz

    @staticmethod
    def delete(quiz: Quiz) -> None:
        db.session.delete(quiz)
        db.session.commit()
