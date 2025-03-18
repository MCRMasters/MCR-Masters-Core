from unittest.mock import patch

import pytest

from app.api.v1.endpoints.ws_room import RoomWebSocketHandler
from app.core.error import DomainErrorCode, MCRDomainError
from app.schemas.ws import WebSocketMessage, WSActionType


@pytest.mark.asyncio
async def test_room_ws_connection_success(room_ws_client, mocker):
    """방 WebSocket 연결 성공 테스트"""
    # 서비스 모킹
    mock_room_service = mocker.AsyncMock()

    # 서비스 응답 모킹
    user = room_ws_client.test_data["user"]
    room = room_ws_client.test_data["room"]
    room_user = room_ws_client.test_data["room_user"]

    mock_room_service.validate_room_user_connection.return_value = (
        user,
        room,
        room_user,
    )

    # RoomWebSocketHandler 인스턴스 생성
    handler = RoomWebSocketHandler(
        websocket=room_ws_client,
        room_number=room.room_number,
        room_service=mock_room_service,
    )

    # get_user_id_from_token 모킹
    # 여러 패치를 하나의 with 문으로 결합
    with (
        patch(
            "app.api.v1.endpoints.ws_room.get_user_id_from_token", return_value=user.id
        ),
        patch("app.core.room_connection_manager.room_manager.connect") as mock_connect,
        patch(
            "app.core.room_connection_manager.room_manager.broadcast"
        ) as mock_broadcast,
    ):
        # handle_connection 실행의 중단을 방지하기 위한 모킹
        mocker.patch.object(handler, "handle_messages", return_value=None)
        # WebSocketDisconnect 예외 방지
        mocker.patch.object(handler, "handle_disconnection", return_value=None)
        result = await handler.handle_connection()

    # 검증
    assert result is True
    mock_room_service.validate_room_user_connection.assert_called_once()
    mock_connect.assert_called_once()
    mock_broadcast.assert_called_once()


@pytest.mark.asyncio
async def test_room_ws_ping_pong(room_ws_client, mocker):
    """방 WebSocket ping-pong 테스트"""
    # 서비스 모킹
    mock_room_service = mocker.AsyncMock()

    # RoomWebSocketHandler 인스턴스 생성
    handler = RoomWebSocketHandler(
        websocket=room_ws_client,
        room_number=room_ws_client.test_data["room"].room_number,
        room_service=mock_room_service,
    )

    # 필드 설정
    handler.user_id = room_ws_client.test_data["user"].id
    handler.room_id = room_ws_client.test_data["room"].id
    handler.room_user = room_ws_client.test_data["room_user"]

    # ping-pong 메시지 처리
    with patch(
        "app.core.room_connection_manager.room_manager.send_personal_message"
    ) as mock_send:
        await handler.handle_ping({"action": "ping"})

    # 검증
    mock_send.assert_called_once()
    args, _ = mock_send.call_args
    assert args[0]["action"] == WSActionType.PONG
    assert args[0]["status"] == "success"
    assert "pong" in args[0]["data"]["message"]


@pytest.mark.asyncio
async def test_room_ws_ready_status(room_ws_client, mocker):
    """방 WebSocket 준비 상태 변경 테스트"""
    # 서비스 모킹
    mock_room_service = mocker.AsyncMock()

    # 서비스 응답 모킹
    room_user = room_ws_client.test_data["room_user"]
    room_user.is_ready = True
    mock_room_service.update_user_ready_status.return_value = room_user

    # RoomWebSocketHandler 인스턴스 생성
    handler = RoomWebSocketHandler(
        websocket=room_ws_client,
        room_number=room_ws_client.test_data["room"].room_number,
        room_service=mock_room_service,
    )

    # 필드 설정
    handler.user_id = room_ws_client.test_data["user"].id
    handler.room_id = room_ws_client.test_data["room"].id
    handler.room_user = room_ws_client.test_data["room_user"]

    # WebSocketMessage 객체 생성
    message = WebSocketMessage(action="ready", data={"is_ready": True})

    # ready 메시지 처리
    with patch(
        "app.core.room_connection_manager.room_manager.broadcast"
    ) as mock_broadcast:
        await handler.handle_ready(message)

    # 검증
    mock_room_service.update_user_ready_status.assert_called_once_with(
        handler.user_id, handler.room_id, True
    )
    mock_broadcast.assert_called_once()
    args, _ = mock_broadcast.call_args
    assert args[0]["action"] == WSActionType.USER_READY_CHANGED
    assert args[0]["status"] == "success"
    assert args[0]["data"]["user_id"] == str(handler.user_id)
    assert args[0]["data"]["is_ready"] is True


@pytest.mark.asyncio
async def test_room_ws_connection_invalid_token(room_ws_client, mocker):
    """잘못된 토큰으로 방 WebSocket 연결 시도 테스트"""
    # 헤더 모킹 - 토큰 없음
    room_ws_client.headers.get.return_value = None

    # 서비스 모킹
    mock_room_service = mocker.AsyncMock()

    # RoomWebSocketHandler 인스턴스 생성
    handler = RoomWebSocketHandler(
        websocket=room_ws_client,
        room_number=1234,
        room_service=mock_room_service,
    )

    # 연결 시도
    result = await handler.handle_connection()

    # 검증
    assert result is False
    room_ws_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_room_ws_connection_room_not_found(room_ws_client, mocker):
    """존재하지 않는 방에 WebSocket 연결 시도 테스트"""
    # 서비스 모킹
    mock_room_service = mocker.AsyncMock()

    # 에러 설정
    error = MCRDomainError(
        code=DomainErrorCode.ROOM_NOT_FOUND,
        message="Room not found",
    )
    mock_room_service.validate_room_user_connection.side_effect = error

    # RoomWebSocketHandler 인스턴스 생성
    handler = RoomWebSocketHandler(
        websocket=room_ws_client,
        room_number=9999,  # 존재하지 않는 방 번호
        room_service=mock_room_service,
    )

    # 연결 시도
    result = await handler.handle_connection()

    # 검증
    assert result is False
    room_ws_client.close.assert_called_once()
