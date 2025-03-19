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

    async def generate_unique_uid(self, max_attempts: int = 10) -> str:
        for _ in range(max_attempts):
            uid = validate_uid(str(randint(100000000, 999999999)))

            count = await self.user_repository.count(uid=uid)
            if count == 0:
                return uid

        raise MCRDomainError(
            code=DomainErrorCode.UID_CREATE_FAILED,
            message=f"Cannot create uid after {max_attempts} tries",
            details={
                "max_attempts": max_attempts,
            },
        )

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
