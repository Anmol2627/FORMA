from backend.app.repositories.quiz_repo import QuizRepository
from backend.app.repositories.attempt_repo import AttemptRepository
from backend.app.schemas.attempt import AttemptSubmitSchema
from backend.app.utils.errors import NotFoundError, ForbiddenError, BadRequestError


class AttemptService:
    def __init__(self, attempt_repo: AttemptRepository = None, quiz_repo: QuizRepository = None):
        self.attempt_repo = attempt_repo or AttemptRepository()
        self.quiz_repo = quiz_repo or QuizRepository()

    def submit_attempt(self, quiz_id: str, user_id: str, submission: AttemptSubmitSchema) -> dict:
        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise NotFoundError(f"Quiz '{quiz_id}' was not found.", code="quiz_not_found")

        # Check access permission
        if quiz.visibility == "private" and quiz.owner_id != user_id:
            raise ForbiddenError("You do not have permission to attempt this quiz.", code="forbidden_quiz_access")

        quiz_questions = {q.id: q for q in quiz.questions}
        total_questions = len(quiz_questions)

        # Build map of submitted answers: question_id -> selected_option_id
        submitted_map = {}
        for item in submission.answers:
            if item.question_id not in quiz_questions:
                raise BadRequestError(
                    f"Question ID '{item.question_id}' does not belong to this quiz.",
                    code="invalid_question_reference"
                )
            submitted_map[item.question_id] = item.selected_option_id

        evaluated_answers = []
        score = 0

        # Evaluate all questions in the quiz
        for q_id, question in quiz_questions.items():
            valid_option_ids = {opt.id: opt for opt in question.options}
            selected_opt_id = submitted_map.get(q_id)

            is_correct = False
            if selected_opt_id:
                if selected_opt_id not in valid_option_ids:
                    raise BadRequestError(
                        f"Selected option '{selected_opt_id}' does not belong to question '{q_id}'.",
                        code="invalid_option_reference"
                    )
                chosen_opt = valid_option_ids[selected_opt_id]
                if chosen_opt.is_correct:
                    is_correct = True
                    score += 1

            evaluated_answers.append({
                "question_id": q_id,
                "selected_option_id": selected_opt_id,
                "is_correct": is_correct
            })

        attempt = self.attempt_repo.create_attempt_with_answers(
            user_id=user_id,
            quiz_id=quiz_id,
            total_questions=total_questions,
            score=score,
            evaluated_answers=evaluated_answers
        )

        return attempt.to_summary_dict()

    def get_attempt_results(self, attempt_id: str, user_id: str) -> dict:
        attempt = self.attempt_repo.get_by_id(attempt_id)
        if not attempt:
            raise NotFoundError(f"Attempt '{attempt_id}' was not found.", code="attempt_not_found")

        # Crucial security boundary: only attempt owner can review answers
        if attempt.user_id != user_id:
            raise ForbiddenError("You are not authorized to view the results of this attempt.", code="forbidden_attempt_access")

        return attempt.to_results_dict()
