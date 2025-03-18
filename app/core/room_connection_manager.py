from uuid import UUID

from fastapi import WebSocket


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

    def disconnect(self, room_id: UUID, user_id: UUID) -> None:
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
            await self.active_connections[room_id][user_id].send_json(message)

    async def broadcast(
        self, message: dict, room_id: UUID, exclude_user_id: UUID | None = None
    ) -> None:
        if room_id in self.active_connections:
            for user_id, connection in self.active_connections[room_id].items():
                if exclude_user_id is None or user_id != exclude_user_id:
                    await connection.send_json(message)

    def get_room_users(self, room_id: UUID) -> set[UUID]:
        if room_id in self.active_connections:
            return set(self.active_connections[room_id].keys())
        return set()

    def is_user_in_room(self, room_id: UUID, user_id: UUID) -> bool:
        return (
            room_id in self.active_connections
            and user_id in self.active_connections[room_id]
        )


room_manager = RoomConnectionManager()
