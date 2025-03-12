from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.room_repository import RoomRepository
from app.repositories.room_user_repository import RoomUserRepository
from app.repositories.user_repository import UserRepository


def get_user_repository(session: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


def get_room_repository(session: AsyncSession = Depends(get_session)) -> RoomRepository:
    return RoomRepository(session)


def get_room_user_repository(
    session: AsyncSession = Depends(get_session),
) -> RoomUserRepository:
    return RoomUserRepository(session)
