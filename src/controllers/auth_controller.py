from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.rate_limit import login_limiter
from src.repositories.user_repository import UserRepository
from src.schemas.auth import LoginRequest, LoginResponse
from src.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    body: LoginRequest,
    session: AsyncSession = Depends(get_db),
):
    login_limiter.check(request)

    service = AuthService(UserRepository(session))
    result = await service.login(body.email, body.password)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user, token = result
    return LoginResponse(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
    )