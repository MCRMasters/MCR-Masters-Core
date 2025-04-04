from unittest.mock import patch

import pytest

from app.api.v1.endpoints.ws_room import RoomWebSocketHandler
from app.core.error import DomainErrorCode, MCRDomainError
from app.schemas.ws import WebSocketMessage, WSActionType


@pytest.mark.asyncio
async def test_connection_success(room_ws_client, mocker):
    mock_room_service = mocker.AsyncMock()

    user = room_ws_client.test_data["user"]
    room = room_ws_client.test_data["room"]
    room_user = room_ws_client.test_data["room_user"]

    mock_room_service.validate_room_user_connection.return_value = (
        user,
        room,
        room_user,
    )

    handler = RoomWebSocketHandler(
        websocket=room_ws_client,
        room_number=room.room_number,
        room_service=mock_room_service,
    )

    with (
        patch(
            "app.api.v1.endpoints.ws_room.get_user_id_from_token", return_value=user.id
        ),
        patch("app.core.room_connection_manager.room_manager.connect") as mock_connect,
        patch(
            "app.core.room_connection_manager.room_manager.broadcast"
        ) as mock_broadcast,
    ):
        mocker.patch.object(handler, "handle_messages", return_value=None)

        mocker.patch.object(handler, "handle_disconnection", return_value=None)
        result = await handler.handle_connection()

    assert result
    mock_room_service.validate_room_user_connection.assert_called_once()
    mock_connect.assert_called_once()
    mock_broadcast.assert_called_once()


@pytest.mark.asyncio
async def test_ping_pong(room_ws_client, mocker):
    mock_room_service = mocker.AsyncMock()

    handler = RoomWebSocketHandler(
        websocket=room_ws_client,
        room_number=room_ws_client.test_data["room"].room_number,
        room_service=mock_room_service,
    )

    handler.user_id = room_ws_client.test_data["user"].id
    handler.room_id = room_ws_client.test_data["room"].id
    handler.room_user = room_ws_client.test_data["room_user"]

    with patch(
        "app.core.room_connection_manager.room_manager.send_personal_message"
    ) as mock_send:
        await handler.handle_ping({"action": "ping"})

    mock_send.assert_called_once()
    args, _ = mock_send.call_args
    assert args[0]["action"] == WSActionType.PONG
    assert args[0]["status"] == "success"
    assert "pong" in args[0]["data"]["message"]


@pytest.mark.asyncio
async def test_ready_status(room_ws_client, mocker):
    mock_room_service = mocker.AsyncMock()

    room_user = room_ws_client.test_data["room_user"]
    room_user.is_ready = True
    mock_room_service.update_user_ready_status.return_value = room_user

    handler = RoomWebSocketHandler(
        websocket=room_ws_client,
        room_number=room_ws_client.test_data["room"].room_number,
        room_service=mock_room_service,
    )

    handler.user_id = room_ws_client.test_data["user"].id
    handler.room_id = room_ws_client.test_data["room"].id
    handler.room_user = room_ws_client.test_data["room_user"]
    handler.user_nickname = room_ws_client.test_data["user"].nickname

    message = WebSocketMessage(action="ready", data={"is_ready": True})

    with patch(
        "app.core.room_connection_manager.room_manager.broadcast"
    ) as mock_broadcast:
        await handler.handle_ready(message)

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
async def test_connection_invalid_token(room_ws_client, mocker):
    room_ws_client.headers.get.return_value = None

    mock_room_service = mocker.AsyncMock()

    handler = RoomWebSocketHandler(
        websocket=room_ws_client,
        room_number=1234,
        room_service=mock_room_service,
    )

    result = await handler.handle_connection()

    assert not result
    room_ws_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_connection_room_not_found(room_ws_client, mocker):
    mock_room_service = mocker.AsyncMock()

    error = MCRDomainError(
        code=DomainErrorCode.ROOM_NOT_FOUND,
        message="Room not found",
    )
    mock_room_service.validate_room_user_connection.side_effect = error

    handler = RoomWebSocketHandler(
        websocket=room_ws_client,
        room_number=9999,
        room_service=mock_room_service,
    )

    result = await handler.handle_connection()

    assert not result
    room_ws_client.close.assert_called_once()
