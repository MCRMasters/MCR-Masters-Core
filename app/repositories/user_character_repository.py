from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import DomainErrorCode
from app.models.user_character import UserCharacter
from app.repositories.base_repository import BaseRepository


class UserCharacterRepository(BaseRepository[UserCharacter]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserCharacter, DomainErrorCode.CHARACTER_NOT_OWNED)

    async def get(self, user_id: UUID, character_code: str) -> UserCharacter | None:
        return await self.filter_one(user_id=user_id, character_code=character_code)

    async def get_or_raise(self, user_id: UUID, character_code: str) -> UserCharacter:
        return await self.filter_one_or_raise(
            user_id=user_id, character_code=character_code
        )

    async def remove(self, user_id: UUID, character_code: str) -> None:
        uc = await self.get_or_raise(user_id, character_code)
        await self.session.delete(uc)
        await self.session.flush()
