import random
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.room import Room
from app.models.room_user import RoomUser
from app.repositories.room_repository import RoomRepository
from app.repositories.room_user_repository import RoomUserRepository
from app.repositories.user_repository import UserRepository


class RoomService:
    def __init__(
        self,
        session: AsyncSession,
        room_repository: RoomRepository | None = None,
        room_user_repository: RoomUserRepository | None = None,
        user_repository: UserRepository | None = None,
    ):
        self.session = session
        self.room_repository = room_repository or RoomRepository(session)
        self.room_user_repository = room_user_repository or RoomUserRepository(session)
        self.user_repository = user_repository or UserRepository(session)

    def _generate_random_room_name(self) -> str:
        adjectives = ["엄숙한", "치열한", "고요한", "은은한", "화려한"]
        nouns = ["패황전", "국작당", "화룡사", "청죽관", "용봉장"]

        adj = random.choice(adjectives)
        noun = random.choice(nouns)

        return f"{adj} {noun}"

    async def create_room(self, user_id: UUID) -> Room:
        user = await self.user_repository.get_by_uuid(user_id)
        if not user:
            raise MCRDomainError(
                code=DomainErrorCode.USER_NOT_FOUND,
                message=f"User with ID {user_id} not found",
                details={"user_id": str(user_id)},
            )

        existing_room_user = await self.room_user_repository.get_by_user(user_id)
        if existing_room_user:
            raise MCRDomainError(
                code=DomainErrorCode.USER_ALREADY_IN_ROOM,
                message="User is already in a room",
                details={
                    "user_id": str(user_id),
                    "room_id": str(existing_room_user.room_id),
                },
            )

        room = Room(
            name=self._generate_random_room_name(),
            max_users=4,
            is_playing=False,
            host_id=user_id,
        )

        created_room = await self.room_repository.create(room)

        room_user = RoomUser(
            room_id=created_room.id,
            user_id=user_id,
            is_ready=True,
        )

        await self.room_user_repository.create(room_user)
        await self.session.commit()

        return created_room
