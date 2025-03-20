from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import DomainErrorCode
from app.models.room_user import RoomUser
from app.repositories.base_repository import BaseRepository


class RoomUserRepository(BaseRepository[RoomUser]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, RoomUser, DomainErrorCode.USER_NOT_IN_ROOM)
