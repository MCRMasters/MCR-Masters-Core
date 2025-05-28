from random import randint
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.character import Character
from app.models.user import User
from app.models.user_character import UserCharacter
from app.repositories.character_repository import CharacterRepository
from app.repositories.user_character_repository import UserCharacterRepository
from app.repositories.user_repository import UserRepository
from app.util.validators import validate_uid


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserRepository | None = None,
        character_repository: CharacterRepository | None = None,
        user_character_repository: UserCharacterRepository | None = None,
    ):
        self.session = session
        self.user_repository = user_repository or UserRepository(session)
        self.character_repository = character_repository or CharacterRepository(session)
        self.user_character_repository = (
            user_character_repository or UserCharacterRepository(session)
        )

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
        existing_user = await self.user_repository.filter_one(email=user_info["email"])

        if not existing_user:
            new_uid = await self.generate_unique_uid()
            new_user = User(
                email=user_info["email"],
                uid=new_uid,
                nickname="",
            )
            created_user = await self.user_repository.create(new_user)
            default_uc = UserCharacter(
                user_id=created_user.id,
                character_code=Character.DEFAULT_CHARACTER_CODE,
            )
            self.session.add(default_uc)
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

    async def toggle_owned_character(self, user_id: UUID, character_code: str) -> bool:
        await self.character_repository.get_by_code_or_raise(code=character_code)

        existing = await self.user_character_repository.get(
            user_id=user_id, character_code=character_code
        )

        if existing:
            await self.user_character_repository.remove(
                user_id=user_id, character_code=character_code
            )
            await self.session.commit()
            return False

        uc = UserCharacter(user_id=user_id, character_code=character_code)
        await self.user_character_repository.create(uc)
        await self.session.commit()
        return True

    async def set_current_character(self, user_id: UUID, character_code: str) -> User:
        character = await self.character_repository.get_by_code_or_raise(character_code)

        user = await self.user_repository.get_by_uuid(user_id)
        if not user:
            raise MCRDomainError(
                code=DomainErrorCode.USER_NOT_FOUND,
                message=f"User {user_id} not found",
                details={"user_id": str(user_id)},
            )

        owned_codes = {c.code for c in user.owned_characters}
        if character_code not in owned_codes:
            raise MCRDomainError(
                code=DomainErrorCode.CHARACTER_NOT_OWNED,
                message=f"User does not own character {character_code}",
                details={"character_code": character_code},
            )

        user.character_code = character.code
        updated = await self.user_repository.update(user)
        await self.session.commit()
        return updated

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        return await self.user_repository.filter_one(id=user_id)

    async def get_user_by_id_with_character_and_owned(
        self, user_id: UUID
    ) -> User | None:
        return await self.user_repository.get_by_uuid_with_options(
            user_id,
            selectinload(User.character),
            selectinload(User.owned_characters),
        )

    async def generate_unique_bot_uid(
        self, prefix: str = "bot-", max_attempts: int = 10
    ) -> str:
        for _ in range(max_attempts):
            candidate = f"{prefix}{uuid4().hex[:8]}"
            if await self.user_repository.count(uid=candidate) == 0:
                return candidate
        raise MCRDomainError(
            code=DomainErrorCode.UID_CREATE_FAILED,
            message=f"Cannot create unique bot uid after {max_attempts} attempts",
            details={"prefix": prefix, "max_attempts": max_attempts},
        )

    async def create_bot_user(self) -> User:
        bot_uid = await self.generate_unique_bot_uid()
        bot = User(
            email=None,
            uid=bot_uid,
            nickname="Bot(Easy)",
            character_code=Character.DEFAULT_CHARACTER_CODE,
        )
        created = await self.user_repository.create(bot)

        default_uc = UserCharacter(
            user_id=created.id,
            character_code=Character.DEFAULT_CHARACTER_CODE,
        )
        self.session.add(default_uc)
        await self.session.commit()
        return created
