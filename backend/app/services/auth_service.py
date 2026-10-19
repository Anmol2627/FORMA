from flask_jwt_extended import create_access_token
from backend.app.repositories.user_repo import UserRepository
from backend.app.schemas.auth import RegisterRequest, LoginRequest
from backend.app.utils.errors import ConflictError, UnauthorizedError, NotFoundError


class AuthService:
    def __init__(self, user_repo: UserRepository = None):
        self.user_repo = user_repo or UserRepository()

    def register(self, req: RegisterRequest) -> dict:
        existing = self.user_repo.get_by_email(req.email)
        if existing:
            raise ConflictError(f"A user with email '{req.email}' already exists.", code="user_already_exists")

        user = self.user_repo.create(
            email=req.email,
            display_name=req.display_name,
            password=req.password
        )
        access_token = create_access_token(identity=user.id)
        return {
            "user": user.to_dict(),
            "access_token": access_token
        }

    def login(self, req: LoginRequest) -> dict:
        user = self.user_repo.get_by_email(req.email)
        if not user or not user.check_password(req.password):
            raise UnauthorizedError("Invalid email or password", code="invalid_credentials")

        if user.account_status != "active":
            raise UnauthorizedError("This account has been deactivated", code="account_inactive")

        access_token = create_access_token(identity=user.id)
        return {
            "user": user.to_dict(),
            "access_token": access_token
        }

    def get_current_user_profile(self, user_id: str) -> dict:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found", code="user_not_found")
        return user.to_dict()
