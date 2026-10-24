from backend.app.repositories.attempt_repo import AttemptRepository


class ProgressService:
    def __init__(self, attempt_repo: AttemptRepository = None):
        self.attempt_repo = attempt_repo or AttemptRepository()

    def get_user_progress(self, user_id: str) -> dict:
        return self.attempt_repo.get_user_progress_stats(user_id=user_id)
