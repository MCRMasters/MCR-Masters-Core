from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room
from app.repositories.base_repository import BaseRepository


class RoomRepository(BaseRepository[Room]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Room)

    async def get_by_room_number(self, room_number: str) -> Room | None:
        result = await self.session.execute(
            select(Room).where(Room.room_number == room_number),
        )
        return cast(Room | None, result.scalar_one_or_none())

    async def get_available_rooms(self) -> list[Room]:
        result = await self.session.execute(
            select(Room).where(not Room.is_playing),
        )
        return cast(list[Room], result.scalars().all())
