from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.encoders import jsonable_encoder
from fastapi.websockets import WebSocketState
from pydantic import ValidationError
from sqlalchemy.orm import selectinload

from app.core.error import MCRDomainError
from app.core.room_connection_manager import room_manager
from app.core.security import get_user_id_from_token
from app.dependencies.services import get_room_service
from app.models.room_user import RoomUser
from app.models.user import User
from app.schemas.character import CharacterResponse
from app.schemas.ws import (
    UserJoinedData,
    UserLeftData,
    UserListData,
    UserReadyData,
    WebSocketMessage,
    WebSocketResponse,
    WSActionType,
)
from app.services.room_service import RoomService

router = APIRouter()


class RoomWebSocketHandler:
    def __init__(
        self, websocket: WebSocket, room_number: int, room_service: RoomService
    ):
        self.websocket = websocket
        self.room_number = room_number
        self.room_service = room_service
        self.user_id: UUID | None = None
        self.room_id: UUID | None = None
        self.user: User | None = None
        self.room_user: RoomUser | None = None

    async def handle_connection(self):
        result = True
        try:
            token = self.websocket.query_params.get("authorization")
            if not token:
                await self.websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                result = False
            else:
                user_id = get_user_id_from_token(token)
                if not user_id:
                    await self.websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    result = False
                else:
                    (
                        self.user,
                        room,
                        self.room_user,
                    ) = await self.room_service.validate_room_user_connection(
                        user_id, self.room_number
                    )

                    self.user_id = self.user.id
                    self.room_id = room.id

                    await room_manager.connect(
                        self.websocket, self.room_id, self.user_id
                    )

                    if self.user is None or self.room_user is None:
                        await self.websocket.send_json(
                            jsonable_encoder(
                                WebSocketResponse(
                                    status="error",
                                    action=WSActionType.ERROR,
                                    error="User or room user data is missing",
                                )
                            )
                        )
                        await self.websocket.close(code=status.WS_1011_INTERNAL_ERROR)
                        result = False
                    else:
                        join_data = UserJoinedData(
                            user_uid=self.user.uid,
                            nickname=self.user.nickname,
                            is_ready=self.room_user.is_ready,
                            slot_index=self.room_user.slot_index,
                            current_character=CharacterResponse(
                                code=self.room_user.character.code,
                                name=self.room_user.character.name,
                            ),
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
            result = False
        except WebSocketDisconnect:
            await self.handle_disconnection()
            result = False
        except Exception as e:
            await self.handle_error(e)
            result = False

        return result

    async def handle_messages(self):
        while True:
            data = await self.websocket.receive_json()
            try:
                message = WebSocketMessage(
                    action=data.get("action", ""), data=data.get("data")
                )
            except ValidationError as e:
                await self.websocket.send_json(
                    jsonable_encoder(
                        WebSocketResponse(
                            status="error",
                            action=WSActionType.ERROR,
                            error=f"Invalid message format: {e!s}",
                        )
                    )
                )
                continue

            message_handlers = {
                WSActionType.PING: self.handle_ping,
                WSActionType.READY: self.handle_ready,
                WSActionType.LEAVE: self.handle_leave,
                WSActionType.ADD_BOT: self.handle_add_bot,
            }

            handler = message_handlers.get(message.action)
            if handler and self.user_id and self.room_id and self.room_user:
                await handler(message)
            else:
                await self.websocket.send_json(
                    jsonable_encoder(
                        WebSocketResponse(
                            status="error",
                            action=WSActionType.ERROR,
                            error=f"Unknown action: {message.action}",
                        )
                    )
                )

    async def handle_add_bot(self, message: WebSocketMessage):
        slot_index: int | None = None

        raw = None
        if message.data:
            raw = message.data.get("slot_index")

        if isinstance(raw, int):
            slot_index = raw
        elif isinstance(raw, str):
            try:
                slot_index = int(raw)
            except ValueError:
                slot_index = None

        if slot_index is None or slot_index < 0:
            await self.websocket.send_json(
                jsonable_encoder(
                    WebSocketResponse(
                        status="error",
                        action=WSActionType.ERROR,
                        error=f"invalid slot index {slot_index}",
                    )
                )
            )
            return

        if self.user_id is None or self.room_id is None:
            await self.websocket.send_json(
                jsonable_encoder(
                    WebSocketResponse(
                        status="error",
                        action=WSActionType.ERROR,
                        error="Internal server error: no user_id or room_id",
                    )
                )
            )
            return

        host_id: UUID = self.user_id
        room_id: UUID = self.room_id

        try:
            await self.room_service.add_bot_to_slot(
                host_id=host_id,
                room_id=room_id,
                slot_index=slot_index,
            )
        except MCRDomainError as e:
            await self.websocket.send_json(
                jsonable_encoder(
                    WebSocketResponse(
                        status="error",
                        action=WSActionType.ERROR,
                        error=str(e),
                    )
                )
            )
            return

        ru_db = await self.room_service.room_user_repository.filter_one_with_options(
            room_id=room_id,
            slot_index=slot_index,
            load_options=[selectinload(RoomUser.character)],
        )

        if ru_db is None:
            await self.websocket.send_json(
                jsonable_encoder(
                    WebSocketResponse(
                        status="error",
                        action=WSActionType.ERROR,
                        error=f"No room user found in slot {slot_index}",
                    )
                )
            )
            return

        join_data = UserJoinedData(
            user_uid=ru_db.user_uid,
            nickname=ru_db.user_nickname,
            is_ready=ru_db.is_ready,
            slot_index=ru_db.slot_index,
            current_character=CharacterResponse(
                code=ru_db.character_code,
                name=ru_db.character.name,
            ),
        )

        await room_manager.broadcast(
            jsonable_encoder(
                WebSocketResponse(
                    status="success",
                    action=WSActionType.USER_JOINED,
                    data=join_data.model_dump(),
                )
            ),
            room_id,
        )

    async def handle_ping(self, _: WebSocketMessage):
        if self.room_id and self.user_id:
            await room_manager.send_personal_message(
                jsonable_encoder(
                    WebSocketResponse(
                        status="success",
                        action=WSActionType.PONG,
                        data={"message": "pong"},
                    )
                ),
                self.room_id,
                self.user_id,
            )

    async def handle_ready(self, message: WebSocketMessage):
        if self.user is None:
            await self.websocket.send_json(
                jsonable_encoder(
                    WebSocketResponse(
                        status="error",
                        action=WSActionType.ERROR,
                        error="User data is missing.",
                    )
                )
            )
            return

        if self.room_user and self.room_id and self.user_id:
            is_ready = message.data.get("is_ready", False) if message.data else False

            updated_room_user = await self.room_service.update_user_ready_status(
                self.user_id, self.room_id, is_ready
            )

            ready_data = UserReadyData(
                user_uid=self.user.uid, is_ready=updated_room_user.is_ready
            )

            await room_manager.broadcast(
                jsonable_encoder(
                    WebSocketResponse(
                        status="success",
                        action=WSActionType.USER_READY_CHANGED,
                        data=ready_data.model_dump(),
                    )
                ),
                self.room_id,
            )

    async def handle_leave(self, _: WebSocketMessage):
        if self.user_id is None or self.room_id is None or self.user is None:
            await self.websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
            return

        new_list = await self.room_service.leave_room(self.user_id, self.room_id)

        if not new_list:
            await room_manager.disconnect(
                room_id=self.room_id,
                user_id=self.user_id,
                session=self.room_service.session,
                room_repository=self.room_service.room_repository,
            )
            await self.websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
            return

        left_data = UserLeftData(user_uid=self.user.uid)
        await room_manager.broadcast(
            WebSocketResponse(
                status="success",
                action=WSActionType.USER_LEFT,
                data=left_data.model_dump(),
            ).model_dump(),
            self.room_id,
        )

        user_list_data = UserListData(users=[u.model_dump() for u in new_list])
        await room_manager.broadcast(
            WebSocketResponse(
                status="success",
                action=WSActionType.USER_LIST,
                data=user_list_data.model_dump(),
            ).model_dump(),
            self.room_id,
        )

        await room_manager.disconnect(
            room_id=self.room_id,
            user_id=self.user_id,
            session=self.room_service.session,
            room_repository=self.room_service.room_repository,
        )
        await self.websocket.close(code=status.WS_1000_NORMAL_CLOSURE)

    async def handle_disconnection(self):
        if not (self.room_id and self.user_id):
            return
        try:
            new_list = await self.room_service.leave_room(
                user_id=self.user_id,
                room_id=self.room_id,
                disconnect_only=True,
            )
        except MCRDomainError:
            new_list = []
        if new_list:
            left_data = UserLeftData(user_uid=self.user.uid)
            await room_manager.broadcast(
                WebSocketResponse(
                    status="success",
                    action=WSActionType.USER_LEFT,
                    data=left_data.model_dump(),
                ).model_dump(),
                self.room_id,
            )
            user_list_data = UserListData(users=[u.model_dump() for u in new_list])
            await room_manager.broadcast(
                WebSocketResponse(
                    status="success",
                    action=WSActionType.USER_LIST,
                    data=user_list_data.model_dump(),
                ).model_dump(),
                self.room_id,
            )
        await room_manager.disconnect(
            room_id=self.room_id,
            user_id=self.user_id,
            session=self.room_service.session,
            room_repository=self.room_service.room_repository,
        )

    async def handle_error(self, e: Exception):
        if self.room_id and self.user_id:
            await self.handle_disconnection()
        if self.websocket.client_state == WebSocketState.CONNECTED:
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
