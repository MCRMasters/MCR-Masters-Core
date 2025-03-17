import random
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.room import Room
from app.models.room_user import RoomUser
from app.models.user import User
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
                message=f"User with ID {user_id} is already in a room",
                details={
                    "user_id": str(user_id),
                    "current_room_id": str(existing_room_user.room_id),
                },
            )

        created_room = await self._create_room_internal(user)
        await self._join_room_internal(user, created_room)
        await self.session.commit()
        return created_room

    async def _create_room_internal(self, user: User) -> Room:
        room = Room(
            name=self._generate_random_room_name(),
            max_users=4,
            is_playing=False,
            host_id=user.id,
        )

        created_room = await self.room_repository.create_with_room_number(room)
        return created_room

    async def join_room(self, user_id: UUID, room_id: UUID) -> RoomUser:
        user = await self.user_repository.get_by_uuid(user_id)
        if not user:
            raise MCRDomainError(
                code=DomainErrorCode.USER_NOT_FOUND,
                message=f"User with ID {user_id} not found",
                details={"user_id": str(user_id)},
            )

        room = await self.room_repository.get_by_uuid(room_id)
        if not room:
            raise MCRDomainError(
                code=DomainErrorCode.ROOM_NOT_FOUND,
                message=f"Room with ID {room_id} not found",
                details={"room_id": str(room_id)},
            )

        if room.is_playing:
            raise MCRDomainError(
                code=DomainErrorCode.ROOM_ALREADY_PLAYING,
                message=f"Room with ID {room_id} is already playing",
                details={"room_id": str(room_id)},
            )

        room_users = await self.room_user_repository.get_by_room(room_id)
        if len(room_users) >= room.max_users:
            raise MCRDomainError(
                code=DomainErrorCode.ROOM_IS_FULL,
                message=f"Room with ID {room_id} is full",
                details={"room_id": str(room_id), "max_users": room.max_users},
            )

        existing_room_user = await self.room_user_repository.get_by_user(user_id)
        if existing_room_user:
            raise MCRDomainError(
                code=DomainErrorCode.USER_ALREADY_IN_ROOM,
                message=f"User with ID {user_id} is already in a room",
                details={
                    "user_id": str(user_id),
                    "current_room_id": str(existing_room_user.room_id),
                },
            )

        room_user = await self._join_room_internal(user, room)
        await self.session.commit()
        return room_user

    async def _join_room_internal(self, user: User, room: Room) -> RoomUser:
        is_host = room.host_id == user.id

        room_user = RoomUser(room_id=room.id, user_id=user.id, is_ready=is_host)

        created_room_user = await self.room_user_repository.create(room_user)
        return created_room_user

    async def toggle_ready(self, user_id: UUID, room_id: UUID) -> RoomUser:
        user = await self.user_repository.get_by_uuid(user_id)
        if not user:
            raise MCRDomainError(
                code=DomainErrorCode.USER_NOT_FOUND,
                message=f"User with ID {user_id} not found",
                details={"user_id": str(user_id)},
            )

        room = await self.room_repository.get_by_uuid(room_id)
        if not room:
            raise MCRDomainError(
                code=DomainErrorCode.ROOM_NOT_FOUND,
                message=f"Room with ID {room_id} not found",
                details={"room_id": str(room_id)},
            )

        room_user = await self.room_user_repository.get_by_user(user_id)
        if not room_user or room_user.room_id != room_id:
            raise MCRDomainError(
                code=DomainErrorCode.USER_NOT_IN_ROOM,
                message=f"User with ID {user_id} is not in room with ID {room_id}",
                details={"user_id": str(user_id), "room_id": str(room_id)},
            )

        if room.host_id == user_id:
            raise MCRDomainError(
                code=DomainErrorCode.HOST_CANNOT_READY,
                message="Host cannot toggle ready status",
                details={"user_id": str(user_id), "room_id": str(room_id)},
            )

        if room.is_playing:
            raise MCRDomainError(
                code=DomainErrorCode.ROOM_ALREADY_PLAYING,
                message=f"Room with ID {room_id} is already playing",
                details={"room_id": str(room_id)},
            )

        updated_room_user = await self._toggle_ready_internal(room_user)
        await self.session.commit()

        return updated_room_user

    async def _toggle_ready_internal(self, room_user: RoomUser) -> RoomUser:
        room_user.is_ready = not room_user.is_ready

        updated_room_user = await self.room_user_repository.update(room_user)
        return updated_room_user

    async def leave_room(self, user_id: UUID) -> None:
        user = await self.user_repository.get_by_uuid(user_id)
        if not user:
            raise MCRDomainError(
                code=DomainErrorCode.USER_NOT_FOUND,
                message=f"User with ID {user_id} not found",
                details={"user_id": str(user_id)},
            )

        room_user = await self.room_user_repository.get_by_user(user_id)
        if not room_user:
            raise MCRDomainError(
                code=DomainErrorCode.USER_NOT_IN_ROOM,
                message=f"User with ID {user_id} is not in any room",
                details={"user_id": str(user_id)},
            )

        room_id = room_user.room_id
        room = await self.room_repository.get_by_uuid(room_id)
        if not room:
            raise MCRDomainError(
                code=DomainErrorCode.ROOM_NOT_FOUND,
                message=f"Room with ID {room_id} not found",
                details={"room_id": str(room_id)},
            )

        if room.is_playing:
            raise MCRDomainError(
                code=DomainErrorCode.ROOM_ALREADY_PLAYING,
                message=f"Cannot leave room with ID {room_id} while playing",
                details={"room_id": str(room_id)},
            )

        await self._leave_room_internal(user, room)

        await self.session.commit()

    async def _leave_room_internal(self, user: User, room: Room) -> None:
        room_id = room.id
        is_host = room.host_id == user.id

        await self.room_user_repository.delete_by_user(user.id)

        room_users = await self.room_user_repository.get_by_room(room_id)

        if not room_users:
            await self.room_repository.delete(room_id)
        elif is_host:
            new_host_user = room_users[0]
            room.host_id = new_host_user.user_id
            await self.room_repository.update(room)

            new_host_user.is_ready = True
            await self.room_user_repository.update(new_host_user)
