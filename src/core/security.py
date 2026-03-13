from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from src.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.app_access_token_expire_minutes
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.app_secret_key, algorithm=settings.app_jwt_algorithm)


def decode_access_token(token: str) -> UUID | None:
    """Returns user_id as UUID if token is valid, None otherwise."""
    try:
        payload = jwt.decode(
            token, settings.app_secret_key, algorithms=[settings.app_jwt_algorithm]
        )
        user_id = payload.get("sub")
        return UUID(user_id) if user_id is not None else None
    except (JWTError, ValueError):
        return None