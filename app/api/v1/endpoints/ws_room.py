import json
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


def debug_print(msg: str):
    print(f"[DEBUG] {msg}")


class RoomWebSocketHandler:
    def __init__(
        self, websocket: WebSocket, room_number: int, room_service: RoomService
    ):
        self.websocket = websocket
        self.room_number = room_number
        self.room_service = room_service

        self.user_id: UUID | None = None
        self.room_id: UUID | None = None
        self.user = None
        self.room_user = None

    async def handle_connection(self):
        debug_print("handle_connection 시작")
        try:
            token = self.websocket.headers.get("authorization")
            debug_print(f"헤더에서 토큰 추출: {token}")
            if not token:
                debug_print("토큰 없음 -> 연결 종료")
                await self.websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return False

            user_id = get_user_id_from_token(token)
            debug_print(f"get_user_id_from_token 결과: {user_id}")
            if not user_id:
                debug_print("토큰으로부터 유효한 user_id 획득 실패")
                await self.websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return False

            debug_print(
                "validate_room_user_connection 호출: "
                "user_id={user_id}, room_number={self.room_number}"
            )
            (
                self.user,
                room,
                self.room_user,
            ) = await self.room_service.validate_room_user_connection(
                user_id, self.room_number
            )
            debug_print(
                f"검증 결과 - user: {self.user}, "
                "room: {room}, room_user: {self.room_user}"
            )

            self.user_id = self.user.id
            self.room_id = room.id
            debug_print(
                "user_id 및 room_id 저장: "
                "user_id={self.user_id}, room_id={self.room_id}"
            )

            debug_print("room_manager.connect 호출")
            await room_manager.connect(
                self.websocket, str(self.room_id), str(self.user_id)
            )
            debug_print("WebSocket 연결 등록 완료")

            join_data = UserJoinedData(
                user_id=str(self.user_id),
                nickname=self.user.nickname,
                is_ready=self.room_user.is_ready,
            )
            debug_print(f"사용자 입장 데이터: {join_data}")
            # model_dump_json()을 사용하여 datetime 등이 문자열로 변환된 dict 생성
            await room_manager.broadcast(
                json.loads(
                    WebSocketResponse(
                        status="success",
                        action=WSActionType.USER_JOINED,
                        data=join_data.model_dump(),
                    ).model_dump_json()
                ),
                str(self.room_id),
                exclude_user_id=str(self.user_id),
            )
            debug_print("사용자 입장 메시지 브로드캐스트 완료")

            await self.handle_messages()

        except MCRDomainError as e:
            debug_print(f"MCRDomainError 발생: {e}")
            await self.websocket.close(
                code=status.WS_1008_POLICY_VIOLATION, reason=str(e)
            )
            return False
        except WebSocketDisconnect:
            debug_print("WebSocketDisconnect 예외 발생")
            await self.handle_disconnection()
            return False
        except Exception as e:
            debug_print(f"handle_connection 중 예외 발생: {e}")
            await self.handle_error(e)
            return False

        debug_print("handle_connection 종료")
        return True

    async def handle_messages(self):
        debug_print("handle_messages 루프 시작")
        while True:
            data = await self.websocket.receive_json()
            debug_print(f"수신한 원시 데이터: {data}")
            try:
                message = WebSocketMessage(
                    action=data.get("action", ""), data=data.get("data")
                )
                debug_print(f"파싱된 메시지: {message}")
            except ValidationError as e:
                debug_print(f"메시지 형식 검증 실패: {e}")
                await self.websocket.send_json(
                    json.loads(
                        WebSocketResponse(
                            status="error",
                            action=WSActionType.ERROR,
                            error=f"Invalid message format: {e!s}",
                        ).model_dump_json()
                    )
                )
                continue

            message_handlers = {
                WSActionType.PING: self.handle_ping,
                WSActionType.READY: self.handle_ready,
                WSActionType.LEAVE: self.handle_leave,
            }
            handler = message_handlers.get(message.action)
            if handler and self.user_id and self.room_id and self.room_user:
                debug_print(f"처리할 메시지 액션: {message.action}")
                await handler(message)
            else:
                debug_print(f"알 수 없거나 처리 불가능한 액션: {message.action}")
                await self.websocket.send_json(
                    json.loads(
                        WebSocketResponse(
                            status="error",
                            action=WSActionType.ERROR,
                            error=f"Unknown action: {message.action}",
                        ).model_dump_json()
                    )
                )

    async def handle_ping(self, _: WebSocketMessage):
        debug_print("handle_ping 호출")
        if self.room_id and self.user_id:
            await room_manager.send_personal_message(
                json.loads(
                    WebSocketResponse(
                        status="success",
                        action=WSActionType.PONG,
                        data={"message": "pong"},
                    ).model_dump_json()
                ),
                str(self.room_id),
                str(self.user_id),
            )
            debug_print("PONG 메시지 전송 완료")

    async def handle_ready(self, message: WebSocketMessage):
        debug_print("handle_ready 호출")
        if self.room_user and self.room_id and self.user_id:
            is_ready_value = (
                message.data.get("is_ready", False) if message.data else False
            )
            debug_print(f"READY 요청: is_ready={is_ready_value}")
            updated_room_user = await self.room_service.update_user_ready_status(
                self.user_id, self.room_id, is_ready_value
            )
            ready_data = UserReadyData(
                user_id=self.user_id,  # UUID 타입 그대로 사용
                nickname=self.user_nickname,
                is_ready=updated_room_user.is_ready,
            )

            await room_manager.broadcast(
                json.loads(
                    WebSocketResponse(
                        status="success",
                        action=WSActionType.USER_READY_CHANGED,
                        data=ready_data.model_dump(),
                    ).model_dump_json()
                ),
                str(self.room_id),
            )
            debug_print("USER_READY_CHANGED 메시지 브로드캐스트 완료")

    async def handle_leave(self, _: WebSocketMessage):
        debug_print("handle_leave 호출, WebSocketDisconnect 발생")
        raise WebSocketDisconnect()

    async def handle_disconnection(self):
        debug_print("handle_disconnection 호출")
        if self.room_id and self.user_id:
            room_manager.disconnect(str(self.room_id), str(self.user_id))
            left_data = UserLeftData(user_id=str(self.user_id))
            await room_manager.broadcast(
                json.loads(
                    WebSocketResponse(
                        status="success",
                        action=WSActionType.USER_LEFT,
                        data=left_data.model_dump(),
                    ).model_dump_json()
                ),
                str(self.room_id),
            )
            debug_print("사용자 퇴장 메시지 브로드캐스트 완료")

    async def handle_error(self, e: Exception):
        debug_print(f"WebSocket error: {e!s}")
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
    print(f"[DEBUG] WebSocket endpoint 호출: room_number={room_number}")
    print("ageegwa")
    handler = RoomWebSocketHandler(websocket, room_number, room_service)
    await handler.handle_connection()
