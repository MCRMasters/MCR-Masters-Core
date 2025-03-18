from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from app.core.error import MCRDomainError
from app.core.room_connection_manager import room_manager
from app.core.security import get_user_id_from_token
from app.dependencies.services import get_room_service
from app.schemas.ws import (
    UserJoinedData,
    UserLeftData,
    UserReadyData,
    WebSocketMessage,
    WebSocketResponse,
    WSActionType,
)
from app.services.room_service import RoomService

router = APIRouter()


class RoomWebSocketHandler:
    def __init__(
        self,
        websocket: WebSocket,
        room_number: int,
        room_service: RoomService,
    ):
        self.websocket = websocket
        self.room_number = room_number
        self.room_service = room_service

        self.user_id: UUID | None = None
        self.room_id: UUID | None = None
        self.user = None
        self.room_user = None

    async def handle_connection(self):
        try:
            token = self.websocket.headers.get("authorization")
            if not token:
                await self.websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return False

            user_id = get_user_id_from_token(token)
            if not user_id:
                await self.websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return False

            (
                self.user,
                room,
                self.room_user,
            ) = await self.room_service.validate_room_user_connection(
                user_id, self.room_number
            )

            self.user_id = self.user.id
            self.room_id = room.id

            await room_manager.connect(self.websocket, self.room_id, self.user_id)

            join_data = UserJoinedData(
                user_id=self.user_id,
                nickname=self.user.nickname,
                is_ready=self.room_user.is_ready,
            )

            await room_manager.broadcast(
                WebSocketResponse(
                    status="success",
                    action=WSActionType.USER_JOINED,
                    data=join_data.model_dump(),
                ).model_dump(),
                self.room_id,
                exclude_user_id=self.user_id,
            )

            await self.handle_messages()

        except MCRDomainError as e:
            await self.websocket.close(
                code=status.WS_1008_POLICY_VIOLATION, reason=str(e)
            )
            return False
        except WebSocketDisconnect:
            await self.handle_disconnection()
            return False
        except Exception as e:
            await self.handle_error(e)
            return False
        finally:
            if self.room_id and self.user_id:
                room_manager.disconnect(self.room_id, self.user_id)

        return True

    async def handle_messages(self):
        while True:
            data = await self.websocket.receive_json()

            try:
                message = WebSocketMessage(
                    action=data.get("action", ""), data=data.get("data")
                )
            except ValidationError as e:
                await self.websocket.send_json(
                    WebSocketResponse(
                        status="error",
                        action=WSActionType.ERROR,
                        error=f"Invalid message format: {e!s}",
                    ).model_dump()
                )
                continue

            message_handlers = {
                WSActionType.PING: self.handle_ping,
                WSActionType.READY: self.handle_ready,
                WSActionType.LEAVE: self.handle_leave,
            }

            handler = message_handlers.get(message.action)
            if handler and self.user_id and self.room_id and self.room_user:
                await handler(message)
            else:
                await self.websocket.send_json(
                    WebSocketResponse(
                        status="error",
                        action=WSActionType.ERROR,
                        error=f"Unknown action: {message.action}",
                    ).model_dump()
                )

    async def handle_ping(self, _: WebSocketMessage):
        if self.room_id and self.user_id:
            await room_manager.send_personal_message(
                WebSocketResponse(
                    status="success",
                    action=WSActionType.PONG,
                    data={"message": "pong"},
                ).model_dump(),
                self.room_id,
                self.user_id,
            )

    async def handle_ready(self, message: WebSocketMessage):
        if self.room_user and self.room_id and self.user_id:
            is_ready = message.data.get("is_ready", False) if message.data else False

            updated_room_user = await self.room_service.update_user_ready_status(
                self.user_id, self.room_id, is_ready
            )

            ready_data = UserReadyData(
                user_id=self.user_id, is_ready=updated_room_user.is_ready
            )

            await room_manager.broadcast(
                WebSocketResponse(
                    status="success",
                    action=WSActionType.USER_READY_CHANGED,
                    data=ready_data.model_dump(),
                ).model_dump(),
                self.room_id,
            )

    async def handle_leave(self, _: WebSocketMessage):
        raise WebSocketDisconnect()

    async def handle_disconnection(self):
        if self.room_id and self.user_id:
            room_manager.disconnect(self.room_id, self.user_id)

            left_data = UserLeftData(user_id=self.user_id)

            await room_manager.broadcast(
                WebSocketResponse(
                    status="success",
                    action=WSActionType.USER_LEFT,
                    data=left_data.model_dump(),
                ).model_dump(),
                self.room_id,
            )

    async def handle_error(self, e: Exception):
        print(f"WebSocket error: {e!s}")
        if self.websocket.client_state.CONNECTED:
            await self.websocket.close(
                code=status.WS_1011_INTERNAL_ERROR, reason=str(e)
            )


@router.websocket("/{room_number}")
async def room_websocket(
    websocket: WebSocket,
    room_number: int,
    room_service: RoomService = Depends(get_room_service),
):
    handler = RoomWebSocketHandler(websocket, room_number, room_service)
    await handler.handle_connection()
