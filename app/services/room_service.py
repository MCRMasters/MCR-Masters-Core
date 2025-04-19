import random
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.error import DomainErrorCode, MCRDomainError
from app.core.room_connection_manager import room_manager
from app.models.room import Room
from app.models.room_user import RoomUser
from app.models.user import User
from app.repositories.room_repository import RoomRepository
from app.repositories.room_user_repository import RoomUserRepository
from app.repositories.user_repository import UserRepository
from app.schemas.room import AvailableRoomResponse, RoomUserResponse, RoomUsersResponse


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
        self.user_repository = user_repository or UserRepository(session)
        self.room_user_repository = room_user_repository or RoomUserRepository(session)

    def _generate_random_room_name(self) -> str:
        adjectives = ["엄숙한", "치열한", "고요한", "은은한", "화려한"]
        nouns = ["패황전", "국작당", "화룡사", "청죽관", "용봉장"]

        adj = random.choice(adjectives)
        noun = random.choice(nouns)

        return f"{adj} {noun}"

    async def create_room(self, current_user_id: UUID) -> Room:
        user: User = await self.user_repository.filter_one_or_raise(id=current_user_id)

        await self.user_repository.filter_one_or_raise(id=current_user_id)

        existing_room_user = await self.room_user_repository.filter_one(
            user_id=current_user_id
        )
        if existing_room_user:
            raise MCRDomainError(
                code=DomainErrorCode.USER_ALREADY_IN_ROOM,
                message=f"User with ID {current_user_id} is already in a room",
                details={
                    "user_id": str(current_user_id),
                    "current_room_id": str(existing_room_user.room_id),
                },
            )

        created_room = await self._create_room_internal(current_user_id)
        await self._join_room_internal(user=user, room_id=created_room.id)
        await self.session.commit()
        return created_room

    async def _create_room_internal(self, user_id: UUID) -> Room:
        room = Room(
            name=self._generate_random_room_name(),
            max_users=4,
            is_playing=False,
            host_id=user_id,
        )

        created_room = await self.room_repository.create_with_room_number(room)
        return created_room

    async def join_room(self, user_id: UUID, room_id: UUID) -> RoomUser:
        user: User = await self.user_repository.filter_one_or_raise(id=user_id)

        room = await self.room_repository.filter_one_or_raise(id=room_id)

        if room.is_playing:
            raise MCRDomainError(
                code=DomainErrorCode.ROOM_ALREADY_PLAYING,
                message=f"Room with ID {room_id} is already playing",
                details={"room_id": str(room_id)},
            )

        room_users = await self.room_user_repository.filter(room_id=room_id)
        if len(room_users) >= room.max_users:
            raise MCRDomainError(
                code=DomainErrorCode.ROOM_IS_FULL,
                message=f"Room with ID {room_id} is full",
                details={"room_id": str(room_id), "max_users": room.max_users},
            )

        existing_room_user = await self.room_user_repository.filter_one(user_id=user_id)
        if existing_room_user:
            raise MCRDomainError(
                code=DomainErrorCode.USER_ALREADY_IN_ROOM,
                message=f"User with ID {user_id} is already in a room",
                details={
                    "user_id": str(user_id),
                    "current_room_id": str(existing_room_user.room_id),
                },
            )

        used_slot_indexes: set[int] = set()
        new_slot_index: int = 0
        for room_user in room_users:
            used_slot_indexes.add(room_user.slot_index)
        for index in range(room.max_users):
            if index not in used_slot_indexes:
                new_slot_index = index
                break
        room_user = await self._join_room_internal(
            user=user, room_id=room_id, slot_index=new_slot_index
        )
        await self.session.commit()
        return room_user

    async def _join_room_internal(
        self, user: User, room_id: UUID, slot_index: int = 0
    ) -> RoomUser:
        room_user = RoomUser(
            room_id=room_id,
            user_id=user.id,
            user_uid=user.uid,
            user_nickname=user.nickname,
            slot_index=slot_index,
            is_ready=False,
        )

        created_room_user = await self.room_user_repository.create(room_user)
        return created_room_user

    async def leave_room(self, user_id: UUID, room_id: UUID) -> list[RoomUserResponse]:
        room: Room = await self.room_repository.filter_one_or_raise(id=room_id)
        room_user: RoomUser = await self.room_user_repository.filter_one_or_raise(
            user_id=user_id
        )
        if room_user.room_id != room.id:
            raise MCRDomainError(
                code=DomainErrorCode.USER_NOT_FOUND,
                message="user not found in room",
                details={"user_id": str(user_id), "room_id": str(room_id)},
            )

        await self.room_user_repository.delete(uuid=room_user.id)
        await self.session.commit()

        remaining = await self.room_user_repository.filter(room_id=room_id)

        if remaining and room.host_id == user_id:
            new_host_ru = min(remaining, key=lambda ru: ru.slot_index)
            room.host_id = new_host_ru.user_id
            await self.room_repository.update(room)
            await self.session.commit()

        if not remaining:
            await self.room_repository.delete(room.id)
            await self.session.commit()
            return []

        return [
            RoomUserResponse(
                nickname=ru.user_nickname,
                uid=ru.user_uid,
                is_ready=ru.is_ready,
                slot_index=ru.slot_index,
            )
            for ru in remaining
        ]

    async def get_available_rooms(self) -> list[AvailableRoomResponse]:
        rooms_with_users = await self.room_repository.get_available_rooms_with_users()
        result = []
        for room, room_users in rooms_with_users:
            host_user = await self.user_repository.filter_one_or_raise(id=room.host_id)
            host_nickname = host_user.nickname

            users = []
            for room_user in room_users:
                user = await self.user_repository.filter_one_or_raise(
                    id=room_user.user_id
                )
                users.append(
                    RoomUserResponse(
                        nickname=user.nickname,
                        uid=user.uid,
                        is_ready=room_user.is_ready,
                        slot_index=room_user.slot_index,
                    )
                )

            room_data = AvailableRoomResponse(
                name=room.name,
                room_number=room.room_number,
                max_users=room.max_users,
                current_users=len(room_users),
                host_uid=host_user.uid,
                host_nickname=host_nickname,
                users=users,
            )
            result.append(room_data)

        return result

    async def validate_room_user_connection(
        self, user_id: UUID, room_number: int
    ) -> tuple[User, Room, RoomUser]:
        user = await self.user_repository.filter_one_or_raise(id=user_id)

        room = await self.room_repository.filter_one_or_raise(room_number=room_number)

        room_user = await self.room_user_repository.filter_one(user_id=user_id)
        if not room_user or room_user.room_id != room.id:
            raise MCRDomainError(
                code=DomainErrorCode.USER_ALREADY_IN_ROOM,
                message=f"User with ID {user_id} not in the specified room",
                details={
                    "user_id": str(user_id),
                    "room_number": room_number,
                },
            )

        return user, room, room_user

    async def update_user_ready_status(
        self, user_id: UUID, room_id: UUID, is_ready: bool
    ) -> RoomUser:
        room_user = await self.room_user_repository.filter_one(user_id=user_id)
        if not room_user or room_user.room_id != room_id:
            raise MCRDomainError(
                code=DomainErrorCode.USER_NOT_FOUND,
                message="User not found in the specified room",
                details={
                    "user_id": str(user_id),
                    "room_id": str(room_id),
                },
            )

        room_user.is_ready = is_ready
        updated_room_user = await self.room_user_repository.update(room_user)
        await self.session.commit()
        return updated_room_user

    async def get_room_users(self, room_id: UUID) -> RoomUsersResponse:
        room: Room = await self.room_repository.filter_one_or_raise(id=room_id)
        room_users = await self.room_user_repository.filter(room_id=room_id)

        users = [
            RoomUserResponse(
                nickname=ru.user_nickname,
                uid=ru.user_uid,
                is_ready=ru.is_ready,
                slot_index=ru.slot_index,
            )
            for ru in room_users
        ]

        return RoomUsersResponse(
            host_uid=str(room.host_id),
            users=users,
        )

    async def end_game(self, room_id: UUID) -> Room:
        room = await self.room_repository.filter_one_or_raise(id=room_id)

        if not room.is_playing:
            raise MCRDomainError(
                code=DomainErrorCode.ROOM_NOT_PLAYING,
                message=f"Room with ID {room_id} is not currently playing",
                details={"room_id": str(room_id)},
            )

        room.is_playing = False
        updated_room = await self.room_repository.update(room)

        room_users = await self.room_user_repository.filter(room_id=room_id)

        for room_user in room_users:
            if room_user.user_id != room.host_id:
                room_user.is_ready = False
                await self.room_user_repository.update(room_user)

        await self.session.commit()
        return updated_room

    async def start_game(self, room_id: UUID) -> Room:
        room = await self.room_repository.filter_one_or_raise(id=room_id)

        if room.is_playing:
            raise MCRDomainError(
                code=DomainErrorCode.ROOM_ALREADY_PLAYING,
                message=f"Room with ID {room_id} is already playing",
                details={"room_id": str(room_id)},
            )

        room_users = await self.room_user_repository.filter(room_id=room_id)
        if len(room_users) < 4:
            raise MCRDomainError(
                code=DomainErrorCode.NOT_ENOUGH_PLAYERS,
                message=f"Room with ID {room_id} does not have enough players",
                details={"room_id": str(room_id), "current_players": len(room_users)},
            )

        not_ready_users = [ru for ru in room_users if not ru.is_ready]
        if not_ready_users:
            raise MCRDomainError(
                code=DomainErrorCode.PLAYERS_NOT_READY,
                message=f"Not all players are ready in room {room_id}",
                details={
                    "room_id": str(room_id),
                    "not_ready_count": len(not_ready_users),
                },
            )

        game_websocket_url = await self._call_game_server_api()

        room.is_playing = True
        updated_room = await self.room_repository.update(room)
        await self.session.commit()

        await room_manager.broadcast_game_started(room_id, game_websocket_url)
        return updated_room

    @staticmethod
    async def _call_game_server_api() -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.GAME_SERVER_URL}/api/v1/games/start",
                timeout=5.0,
            )
            response.raise_for_status()
            game_data: dict[str, str] = response.json()
            return game_data.get("websocket_url", "")
