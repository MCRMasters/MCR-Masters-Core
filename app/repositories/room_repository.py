from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import DomainErrorCode
from app.models.room import Room
from app.models.room_user import RoomUser
from app.repositories.base_repository import BaseRepository


class RoomRepository(BaseRepository[Room]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Room, DomainErrorCode.ROOM_NOT_FOUND)

    async def _generate_room_number(self) -> int:
        result = await self.session.execute(select(func.max(Room.room_number)))
        max_room_number = result.scalar() or 0
        return max_room_number + 1

    async def create_with_room_number(self, room: Room) -> Room:
        room.room_number = await self._generate_room_number()
        return await self.create(room)

    async def get_available_rooms_with_users(self) -> list[tuple[Room, list[RoomUser]]]:
        result = await self.session.execute(
            select(Room).where(Room.is_playing == False)  # noqa: E712
        )
        rooms = result.scalars().all()

        room_with_users = []
        for room in rooms:
            room_users = await self.session.execute(
                select(RoomUser).where(RoomUser.room_id == room.id)
            )
            room_with_users.append((room, room_users.scalars().all()))

        return room_with_users
