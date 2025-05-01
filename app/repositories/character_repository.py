from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import DomainErrorCode
from app.models.character import Character
from app.repositories.base_repository import BaseRepository


class CharacterRepository(BaseRepository[Character]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Character, DomainErrorCode.CHARACTER_NOT_FOUND)

    async def get_by_code(self, code: str) -> Character | None:
        return await self.filter_one(code=code)

    async def get_by_code_or_raise(self, code: str) -> Character:
        return await self.filter_one_or_raise(code=code)

    async def list_all(
        self, offset: int | None = None, limit: int | None = None
    ) -> list[Character]:
        return await self.filter(offset=offset, limit=limit)
