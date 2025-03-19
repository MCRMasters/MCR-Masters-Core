from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import DomainErrorCode
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User, DomainErrorCode.USER_NOT_FOUND)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email),
        )
        return cast(User | None, result.scalar_one_or_none())

    async def get_by_uid(self, uid: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.uid == uid),
        )
        return cast(User | None, result.scalar_one_or_none())
