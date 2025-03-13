from random import randint
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.util.validators import validate_uid


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserRepository | None = None,
    ):
        self.session = session
        self.user_repository = user_repository or UserRepository(session)

    async def generate_unique_uid(self) -> str:
        while True:
            uid = str(randint(100000000, 999999999))

            try:
                validate_uid(uid)
                existing_user = await self.user_repository.get_by_uid(uid)

                if not existing_user:
                    return uid

            except Exception:
                continue

    async def get_or_create_user(self, user_info: dict[str, Any]) -> tuple[User, bool]:
        existing_user = await self.user_repository.get_by_email(user_info["email"])

        if not existing_user:
            new_uid = await self.generate_unique_uid()
            new_user = User(
                email=user_info["email"],
                uid=new_uid,
                nickname="",
            )
            created_user = await self.user_repository.create(new_user)
            await self.session.commit()
            return created_user, True

        return existing_user, existing_user.nickname == ""

    async def update_nickname(self, user_id: UUID, nickname: str) -> User:
        user = await self.user_repository.get_by_uuid(user_id)

        if not user:
            raise MCRDomainError(
                code=DomainErrorCode.USER_NOT_FOUND,
                message=f"User with ID {user_id} not found",
                details={
                    "user_id": str(user_id),
                },
            )

        if user.nickname.strip():
            raise MCRDomainError(
                code=DomainErrorCode.NICKNAME_ALREADY_SET,
                message="Nickname already set and cannot be changed",
                details={
                    "user_id": str(user_id),
                    "current_nickname": user.nickname,
                },
            )

        user.nickname = nickname
        updated_user = await self.user_repository.update(user)
        await self.session.commit()
        return updated_user
