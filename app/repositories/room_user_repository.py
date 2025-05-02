from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.room_user import RoomUser
from app.repositories.base_repository import BaseRepository


class RoomUserRepository(BaseRepository[RoomUser]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, RoomUser, DomainErrorCode.USER_NOT_IN_ROOM)

    async def get_by_uuid_with_character(self, room_user_id: UUID) -> RoomUser:
        room_user = await self.get_by_uuid_with_options(
            room_user_id,
            selectinload(RoomUser.character),
        )
        if not room_user:
            raise MCRDomainError(
                code=self.not_found_error_code,
                message=f"RoomUser {room_user_id} not found",
                details={"uuid": str(room_user_id)},
            )
        return room_user
