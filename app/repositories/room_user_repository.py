from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room_user import RoomUser
from app.repositories.base_repository import BaseRepository


class RoomUserRepository(BaseRepository[RoomUser]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, RoomUser)

    async def get_by_room(self, room_id: UUID) -> list[RoomUser]:
        result = await self.session.execute(
            select(RoomUser).where(RoomUser.room_id == room_id),
        )
        return cast(list[RoomUser], result.scalars().all())

    async def get_by_user(self, user_id: UUID) -> RoomUser | None:
        result = await self.session.execute(
            select(RoomUser).where(RoomUser.user_id == user_id),
        )
        return cast(RoomUser | None, result.scalar_one_or_none())
