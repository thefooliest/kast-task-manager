from src.core.security import create_access_token, verify_password
from src.domain.user import User
from src.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def login(self, email: str, password: str) -> tuple[User, str] | None:
        """Returns (user, access_token) on success, None on failure."""
        user = await self._user_repo.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            return None

        token = create_access_token(user.id)
        return user, token