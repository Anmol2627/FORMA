from typing import List
from backend.app.repositories.quiz_repo import QuizRepository
from backend.app.schemas.quiz import QuizCreateSchema, QuizUpdateSchema
from backend.app.utils.errors import NotFoundError, ForbiddenError


class QuizService:
    def __init__(self, quiz_repo: QuizRepository = None):
        self.quiz_repo = quiz_repo or QuizRepository()

    def list_quizzes(self, user_id: str, include_public: bool = True) -> List[dict]:
        quizzes = self.quiz_repo.list_accessible(user_id=user_id, include_public=include_public)
        # For listings, omit full question options to keep payload compact
        return [q.to_dict(include_questions=False) for q in quizzes]

    def get_quiz_by_id(self, quiz_id: str, current_user_id: str) -> dict:
        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise NotFoundError(f"Quiz '{quiz_id}' was not found.", code="quiz_not_found")

        # Authorization: private quizzes can only be viewed by their owner
        if quiz.visibility == "private" and quiz.owner_id != current_user_id:
            raise ForbiddenError("You do not have permission to view this private quiz.", code="forbidden_quiz_access")

        return quiz.to_dict(include_questions=True)

    def get_quiz_for_taking(self, quiz_id: str, current_user_id: str) -> dict:
        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise NotFoundError(f"Quiz '{quiz_id}' was not found.", code="quiz_not_found")

        if quiz.visibility == "private" and quiz.owner_id != current_user_id:
            raise ForbiddenError("You do not have permission to access this quiz.", code="forbidden_quiz_access")

        # Critical security boundary: returns take view without answers or explanations
        return quiz.to_take_dict()

    def create_quiz(self, user_id: str, schema: QuizCreateSchema) -> dict:
        questions_payload = []
        for q in schema.questions:
            q_dict = {
                "prompt": q.prompt,
                "explanation": q.explanation,
                "display_position": q.display_position,
                "topic": q.topic,
                "difficulty": q.difficulty,
                "options": [opt.model_dump() for opt in q.options]
            }
            questions_payload.append(q_dict)

        quiz = self.quiz_repo.create(
            owner_id=user_id,
            title=schema.title,
            description=schema.description,
            visibility=schema.visibility,
            generation_metadata=schema.generation_metadata,
            questions_data=questions_payload
        )
        return quiz.to_dict(include_questions=True)

    def update_quiz(self, quiz_id: str, user_id: str, schema: QuizUpdateSchema) -> dict:
        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise NotFoundError(f"Quiz '{quiz_id}' was not found.", code="quiz_not_found")

        if quiz.owner_id != user_id:
            raise ForbiddenError("You are not authorized to modify this quiz.", code="forbidden_quiz_modification")

        questions_payload = None
        if schema.questions is not None:
            questions_payload = []
            for q in schema.questions:
                q_dict = {
                    "prompt": q.prompt,
                    "explanation": q.explanation,
                    "display_position": q.display_position,
                    "topic": q.topic,
                    "difficulty": q.difficulty,
                    "options": [opt.model_dump() for opt in q.options]
                }
                questions_payload.append(q_dict)

        updated_quiz = self.quiz_repo.update(
            quiz=quiz,
            title=schema.title,
            description=schema.description,
            visibility=schema.visibility,
            questions_data=questions_payload
        )
        return updated_quiz.to_dict(include_questions=True)

    def delete_quiz(self, quiz_id: str, user_id: str) -> None:
        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise NotFoundError(f"Quiz '{quiz_id}' was not found.", code="quiz_not_found")

        if quiz.owner_id != user_id:
            raise ForbiddenError("You are not authorized to delete this quiz.", code="forbidden_quiz_deletion")

        self.quiz_repo.delete(quiz)
