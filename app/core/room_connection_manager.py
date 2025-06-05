from uuid import UUID

from fastapi import WebSocket, status
from fastapi.encoders import jsonable_encoder
from fastapi.websockets import WebSocketState
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import DomainErrorCode, MCRDomainError
from app.core.security import get_user_id_from_token
from app.models.user import User
from app.repositories.room_repository import RoomRepository
from app.repositories.room_user_repository import RoomUserRepository
from app.repositories.user_repository import UserRepository
from app.schemas.ws import GameStartedData, WebSocketResponse, WSActionType


class RoomConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[UUID, dict[UUID, WebSocket]] = {}
        self.user_rooms: dict[UUID, UUID] = {}

    async def connect(self, websocket: WebSocket, room_id: UUID, user_id: UUID) -> None:
        await websocket.accept()

        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}

        self.active_connections[room_id][user_id] = websocket
        self.user_rooms[user_id] = room_id

    async def disconnect(
        self,
        room_id: UUID,
        user_id: UUID,
        *,
        session: AsyncSession | None = None,
        room_repository: RoomRepository | None = None,
    ) -> None:
        should_remove = True

        if room_repository and session:
            try:
                room = await room_repository.filter_one_or_raise(id=room_id)
                if room.is_playing:
                    should_remove = False
            except MCRDomainError:
                pass

        if should_remove:
            if (
                room_id in self.active_connections
                and user_id in self.active_connections[room_id]
            ):
                del self.active_connections[room_id][user_id]

                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]

            if user_id in self.user_rooms:
                del self.user_rooms[user_id]

    async def send_personal_message(
        self, message: dict, room_id: UUID, user_id: UUID
    ) -> None:
        if (
            room_id in self.active_connections
            and user_id in self.active_connections[room_id]
        ):
            json_message = jsonable_encoder(message)
            await self.active_connections[room_id][user_id].send_json(json_message)

    async def broadcast(
        self, message: dict, room_id: UUID, exclude_user_id: UUID | None = None
    ) -> None:
        if room_id in self.active_connections:
            json_message = jsonable_encoder(message)
            for user_id, connection in self.active_connections[room_id].items():
                if exclude_user_id is None or user_id != exclude_user_id:
                    try:
                        if connection.client_state == WebSocketState.CONNECTED:
                            await connection.send_json(json_message)
                    except Exception:
                        pass

    async def broadcast_game_started(self, room_id: UUID, ws_url: str) -> None:
        if room_id not in self.active_connections:
            raise MCRDomainError(
                code=DomainErrorCode.ROOM_NOT_FOUND,
                message="room not exist",
                details={"room_id": room_id},
            )
        response = WebSocketResponse(
            status="success",
            action=WSActionType.GAME_STARTED,
            data=GameStartedData(game_url=ws_url).model_dump(),
        )
        json_message = jsonable_encoder(response.model_dump())
        for connection in self.active_connections[room_id].values():
            await connection.send_json(json_message)

    def get_room_users(self, room_id: UUID) -> set[UUID]:
        if room_id in self.active_connections:
            return set(self.active_connections[room_id].keys())
        return set()

    def is_user_in_room(self, room_id: UUID, user_id: UUID) -> bool:
        return (
            room_id in self.active_connections
            and user_id in self.active_connections[room_id]
        )

    @staticmethod
    async def authenticate_and_validate_connection(
        websocket: WebSocket,
        room_number: int,
        room_repository: RoomRepository,
        room_user_repository: RoomUserRepository,
        user_repository: UserRepository,
    ) -> tuple[UUID | None, UUID | None, User | None]:
        token = websocket.headers.get("authorization")
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None, None, None

        user_id = get_user_id_from_token(token)
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None, None, None

        try:
            user = await user_repository.filter_one_or_raise(id=user_id)
            room = await room_repository.filter_one_or_raise(room_number=room_number)
            await room_user_repository.filter_one_or_raise(
                user_id=user_id, room_id=room.id
            )
        except MCRDomainError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None, None, None

        return user_id, room.id, user


room_manager = RoomConnectionManager()
