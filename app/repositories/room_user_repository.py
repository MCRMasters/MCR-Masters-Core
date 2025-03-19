from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import DomainErrorCode
from app.models.room_user import RoomUser
from app.repositories.base_repository import BaseRepository


class RoomUserRepository(BaseRepository[RoomUser]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, RoomUser, DomainErrorCode.USER_NOT_IN_ROOM)

    async def get_by_user(self, user_id: UUID) -> RoomUser | None:
        result = await self.session.execute(
            select(RoomUser).where(RoomUser.user_id == user_id),
        )
        return cast(RoomUser | None, result.scalar_one_or_none())
