from random import randint
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.user import User
from app.util.validators import validate_uid


async def generate_unique_uid(db: AsyncSession) -> str:
    while True:
        uid = str(randint(100000000, 999999999))

        try:
            validate_uid(uid)
            result = await db.execute(
                select(User).where(User.uid == uid),
            )
            existing_user = result.scalar_one_or_none()

            if not existing_user:
                return uid

        except Exception:
            continue


async def get_or_create_user(db: AsyncSession, user_info: dict) -> tuple[User, bool]:
    result = await db.execute(
        select(User).where(User.email == user_info["email"]),
    )
    user: User | None = result.scalar_one_or_none()
    if not user:
        new_uid = await generate_unique_uid(db)
        user = User(
            email=user_info["email"],
            uid=new_uid,
            nickname="",
        )
        db.add(user)
        return user, True

    return user, user.nickname == ""


async def update_nickname(db: AsyncSession, user_id: UUID, nickname: str) -> User:
    result = await db.execute(
        select(User).where(User.id == user_id),
    )
    user: User | None = result.scalar_one_or_none()

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
    return user
