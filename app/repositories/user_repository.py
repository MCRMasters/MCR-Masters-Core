from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User, DomainErrorCode.USER_NOT_FOUND)

    async def get_by_uuid_with_character(self, uuid: UUID) -> User:
        result = await self.get_by_uuid_with_options(
            uuid,
            selectinload(User.character),
        )
        if result is None:
            raise MCRDomainError(
                code=self.not_found_error_code,
                message=f"User {uuid} not found",
                details={"model": "User", "uuid": str(uuid)},
            )
        return result

    async def get_by_uuid_with_character_and_owned(self, user_id: UUID) -> User:
        user = await self.get_by_uuid_with_options(
            user_id,
            selectinload(User.character),
            selectinload(User.owned_characters),
        )
        if not user:
            raise MCRDomainError(
                code=self.not_found_error_code,
                message=f"User {user_id} not found",
                details={"uuid": str(user_id)},
            )
        return user
