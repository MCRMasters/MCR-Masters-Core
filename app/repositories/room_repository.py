from typing import cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room
from app.repositories.base_repository import BaseRepository


class RoomRepository(BaseRepository[Room]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Room)

    async def get_by_room_number(self, room_number: int) -> Room | None:
        result = await self.session.execute(
            select(Room).where(Room.room_number == room_number),
        )
        return cast(Room | None, result.scalar_one_or_none())

    async def get_available_rooms(self) -> list[Room]:
        result = await self.session.execute(
            select(Room).where(Room.is_playing == False),  # noqa: E712
        )
        return cast(list[Room], result.scalars().all())

    async def _generate_room_number(self) -> int:
        result = await self.session.execute(select(func.max(Room.room_number)))
        max_room_number = result.scalar() or 0
        return max_room_number + 1

    async def create_with_room_number(self, room: Room) -> Room:
        room.room_number = await self._generate_room_number()
        return await self.create(room)
