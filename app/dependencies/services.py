from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.dependencies.repositories import get_user_repository
from app.repositories.user_repository import UserRepository
from app.services.auth.google import GoogleOAuthService
from app.services.auth.user_service import UserService


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    session: AsyncSession = Depends(get_session),
) -> UserService:
    return UserService(session, user_repository)


def get_google_oauth_service(
    user_service: UserService = Depends(get_user_service),
    session: AsyncSession = Depends(get_session),
) -> GoogleOAuthService:
    return GoogleOAuthService(session, user_service)
