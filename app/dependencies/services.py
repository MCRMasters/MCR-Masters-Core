from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.dependencies.repositories import (
    get_room_repository,
    get_room_user_repository,
    get_user_repository,
)
from app.repositories.room_repository import RoomRepository
from app.repositories.room_user_repository import RoomUserRepository
from app.repositories.user_repository import UserRepository
from app.services.auth.google import GoogleOAuthService
from app.services.auth.user_service import UserService
from app.services.room_service import RoomService


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


def get_room_service(
    session: AsyncSession = Depends(get_session),
    room_repository: RoomRepository = Depends(get_room_repository),
    room_user_repository: RoomUserRepository = Depends(get_room_user_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    user_service: UserService = Depends(get_user_service),
) -> RoomService:
    return RoomService(
        session=session,
        room_repository=room_repository,
        room_user_repository=room_user_repository,
        user_repository=user_repository,
        user_service=user_service,
    )
