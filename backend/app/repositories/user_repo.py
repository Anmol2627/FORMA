from typing import Optional
from backend.app.extensions import db
from backend.app.models.user import User


class UserRepository:
    @staticmethod
    def get_by_id(user_id: str) -> Optional[User]:
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        return User.query.filter(User.email == email.strip().lower()).first()

    @staticmethod
    def create(email: str, display_name: str, password: str) -> User:
        user = User(
            email=email.strip().lower(),
            display_name=display_name.strip(),
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
