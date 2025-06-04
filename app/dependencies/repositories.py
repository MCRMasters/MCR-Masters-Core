from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.room import Room
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


async def get_room_by_number(
    room_number: int,
    room_repository: RoomRepository = Depends(get_room_repository),
) -> Room:
    return await room_repository.filter_one_or_raise(room_number=room_number)


async def get_room_by_game_id(
    game_id: int,
    room_repository: RoomRepository = Depends(get_room_repository),
) -> Room:
    return await room_repository.filter_one_or_raise(game_id=game_id)
