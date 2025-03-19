import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import WebSocket, status

from app.core.room_connection_manager import RoomConnectionManager
from app.models.room import Room
from app.models.room_user import RoomUser
from app.models.user import User


@pytest.fixture
def room_id():
    return uuid.uuid4()


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def another_user_id():
    return uuid.uuid4()


@pytest.fixture
def mock_websocket():
    return AsyncMock(spec=WebSocket)


@pytest.fixture
def connection_manager():
    manager = RoomConnectionManager()

    yield manager
    manager.active_connections.clear()
    manager.user_rooms.clear()


@pytest.mark.asyncio
async def test_connect(connection_manager, mock_websocket, room_id, user_id):
    await connection_manager.connect(mock_websocket, room_id, user_id)

    mock_websocket.accept.assert_called_once()
    assert user_id in connection_manager.active_connections[room_id]
    assert connection_manager.active_connections[room_id][user_id] == mock_websocket
    assert connection_manager.user_rooms[user_id] == room_id


@pytest.mark.asyncio
async def test_connect_multiple_users(
    connection_manager, room_id, user_id, another_user_id
):
    websocket1 = AsyncMock(spec=WebSocket)
    websocket2 = AsyncMock(spec=WebSocket)

    await connection_manager.connect(websocket1, room_id, user_id)
    await connection_manager.connect(websocket2, room_id, another_user_id)

    assert len(connection_manager.active_connections[room_id]) == 2
    assert connection_manager.active_connections[room_id][user_id] == websocket1
    assert connection_manager.active_connections[room_id][another_user_id] == websocket2
    assert connection_manager.user_rooms[user_id] == room_id
    assert connection_manager.user_rooms[another_user_id] == room_id


@pytest.mark.asyncio
async def test_disconnect(connection_manager, mock_websocket, room_id, user_id):
    await connection_manager.connect(mock_websocket, room_id, user_id)

    connection_manager.disconnect(room_id, user_id)

    assert room_id not in connection_manager.active_connections
    assert user_id not in connection_manager.user_rooms


@pytest.mark.asyncio
async def test_disconnect_with_multiple_users(
    connection_manager, room_id, user_id, another_user_id
):
    websocket1 = AsyncMock(spec=WebSocket)
    websocket2 = AsyncMock(spec=WebSocket)

    await connection_manager.connect(websocket1, room_id, user_id)
    await connection_manager.connect(websocket2, room_id, another_user_id)

    connection_manager.disconnect(room_id, user_id)

    assert room_id in connection_manager.active_connections
    assert user_id not in connection_manager.active_connections[room_id]
    assert another_user_id in connection_manager.active_connections[room_id]
    assert user_id not in connection_manager.user_rooms
    assert connection_manager.user_rooms[another_user_id] == room_id


@pytest.mark.asyncio
async def test_broadcast(connection_manager, room_id, user_id, another_user_id):
    websocket1 = AsyncMock(spec=WebSocket)
    websocket2 = AsyncMock(spec=WebSocket)

    await connection_manager.connect(websocket1, room_id, user_id)
    await connection_manager.connect(websocket2, room_id, another_user_id)

    message = {"status": "success", "action": "test_action", "data": {"test": "data"}}

    await connection_manager.broadcast(message, room_id)

    websocket1.send_json.assert_called_once_with(message)
    websocket2.send_json.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_broadcast_with_exclude(
    connection_manager, room_id, user_id, another_user_id
):
    websocket1 = AsyncMock(spec=WebSocket)
    websocket2 = AsyncMock(spec=WebSocket)

    await connection_manager.connect(websocket1, room_id, user_id)
    await connection_manager.connect(websocket2, room_id, another_user_id)

    message = {"status": "success", "action": "test_action", "data": {"test": "data"}}

    await connection_manager.broadcast(message, room_id, exclude_user_id=user_id)

    websocket1.send_json.assert_not_called()
    websocket2.send_json.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_broadcast_empty_room(connection_manager, room_id):
    message = {"status": "success", "action": "test_action"}

    await connection_manager.broadcast(message, room_id)


@pytest.mark.asyncio
async def test_personal_message(connection_manager, room_id, user_id, another_user_id):
    websocket1 = AsyncMock(spec=WebSocket)
    websocket2 = AsyncMock(spec=WebSocket)

    await connection_manager.connect(websocket1, room_id, user_id)
    await connection_manager.connect(websocket2, room_id, another_user_id)

    message = {"status": "success", "action": "test_action", "data": {"test": "data"}}

    await connection_manager.send_personal_message(message, room_id, user_id)

    websocket1.send_json.assert_called_once_with(message)
    websocket2.send_json.assert_not_called()


@pytest.mark.asyncio
async def test_personal_message_invalid_user(connection_manager, room_id, user_id):
    non_existent_user_id = uuid.uuid4()
    message = {"status": "success", "action": "test_action"}

    websocket = AsyncMock(spec=WebSocket)
    await connection_manager.connect(websocket, room_id, user_id)

    await connection_manager.send_personal_message(
        message, room_id, non_existent_user_id
    )

    websocket.send_json.assert_not_called()


@pytest.mark.asyncio
async def test_personal_message_invalid_room(connection_manager, user_id):
    non_existent_room_id = uuid.uuid4()
    message = {"status": "success", "action": "test_action"}

    await connection_manager.send_personal_message(
        message, non_existent_room_id, user_id
    )


def test_get_room_users(connection_manager, room_id, user_id, another_user_id):
    connection_manager.active_connections[room_id] = {
        user_id: AsyncMock(spec=WebSocket),
        another_user_id: AsyncMock(spec=WebSocket),
    }

    users = connection_manager.get_room_users(room_id)

    assert len(users) == 2
    assert user_id in users
    assert another_user_id in users


def test_get_room_users_empty_room(connection_manager, room_id):
    users = connection_manager.get_room_users(room_id)

    assert len(users) == 0


def test_is_user_in_room(connection_manager, room_id, user_id):
    connection_manager.active_connections[room_id] = {
        user_id: AsyncMock(spec=WebSocket)
    }

    assert connection_manager.is_user_in_room(room_id, user_id) is True
    assert connection_manager.is_user_in_room(room_id, uuid.uuid4()) is False
    assert connection_manager.is_user_in_room(uuid.uuid4(), user_id) is False


@pytest.mark.asyncio
async def test_authenticate_and_validate_connection_success():
    websocket = AsyncMock(spec=WebSocket)
    websocket.headers.get.return_value = "valid_token"

    room_number = 12345
    user_id = uuid.uuid4()
    room_id = uuid.uuid4()

    user = User(id=user_id, uid="123456789", nickname="TestUser")
    room = Room(id=room_id, room_number=room_number, host_id=user_id, name="TestRoom")
    room_user = RoomUser(room_id=room_id, user_id=user_id)

    room_repository = AsyncMock()
    room_repository.get_by_room_number.return_value = room

    room_user_repository = AsyncMock()
    room_user_repository.get_by_user.return_value = room_user

    user_repository = AsyncMock()
    user_repository.get_by_uuid.return_value = user

    with patch(
        "app.core.room_connection_manager.get_user_id_from_token", return_value=user_id
    ):
        result = await RoomConnectionManager.authenticate_and_validate_connection(
            websocket,
            room_number,
            room_repository,
            room_user_repository,
            user_repository,
        )

    assert result == (user_id, room_id, user)
    websocket.close.assert_not_called()


@pytest.mark.asyncio
async def test_authenticate_and_validate_connection_no_token():
    websocket = AsyncMock(spec=WebSocket)
    websocket.headers.get.return_value = None

    room_repository = AsyncMock()
    room_user_repository = AsyncMock()
    user_repository = AsyncMock()

    result = await RoomConnectionManager.authenticate_and_validate_connection(
        websocket, 12345, room_repository, room_user_repository, user_repository
    )

    assert result == (None, None, None)
    websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)


@pytest.mark.asyncio
async def test_authenticate_and_validate_connection_invalid_token():
    websocket = AsyncMock(spec=WebSocket)
    websocket.headers.get.return_value = "invalid_token"

    room_repository = AsyncMock()
    room_user_repository = AsyncMock()
    user_repository = AsyncMock()

    with patch(
        "app.core.room_connection_manager.get_user_id_from_token", return_value=None
    ):
        result = await RoomConnectionManager.authenticate_and_validate_connection(
            websocket, 12345, room_repository, room_user_repository, user_repository
        )

    assert result == (None, None, None)
    websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)


@pytest.mark.asyncio
async def test_authenticate_and_validate_connection_user_not_found():
    websocket = AsyncMock(spec=WebSocket)
    websocket.headers.get.return_value = "valid_token"

    user_id = uuid.uuid4()

    room_repository = AsyncMock()
    room_user_repository = AsyncMock()

    user_repository = AsyncMock()
    user_repository.get_by_uuid.return_value = None

    with patch(
        "app.core.room_connection_manager.get_user_id_from_token", return_value=user_id
    ):
        result = await RoomConnectionManager.authenticate_and_validate_connection(
            websocket, 12345, room_repository, room_user_repository, user_repository
        )

    assert result == (None, None, None)
    websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)


@pytest.mark.asyncio
async def test_authenticate_and_validate_connection_room_not_found():
    websocket = AsyncMock(spec=WebSocket)
    websocket.headers.get.return_value = "valid_token"

    user_id = uuid.uuid4()
    user = User(id=user_id, uid="123456789", nickname="TestUser")

    room_repository = AsyncMock()
    room_repository.get_by_room_number.return_value = None

    room_user_repository = AsyncMock()

    user_repository = AsyncMock()
    user_repository.get_by_uuid.return_value = user

    with patch(
        "app.core.room_connection_manager.get_user_id_from_token", return_value=user_id
    ):
        result = await RoomConnectionManager.authenticate_and_validate_connection(
            websocket, 12345, room_repository, room_user_repository, user_repository
        )

    assert result == (None, None, None)
    websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)


@pytest.mark.asyncio
async def test_authenticate_and_validate_connection_room_user_not_found():
    websocket = AsyncMock(spec=WebSocket)
    websocket.headers.get.return_value = "valid_token"

    user_id = uuid.uuid4()
    room_id = uuid.uuid4()

    user = User(id=user_id, uid="123456789", nickname="TestUser")
    room = Room(id=room_id, room_number=12345, host_id=user_id, name="TestRoom")

    room_repository = AsyncMock()
    room_repository.get_by_room_number.return_value = room

    room_user_repository = AsyncMock()
    room_user_repository.get_by_user.return_value = None

    user_repository = AsyncMock()
    user_repository.get_by_uuid.return_value = user

    with patch(
        "app.core.room_connection_manager.get_user_id_from_token", return_value=user_id
    ):
        result = await RoomConnectionManager.authenticate_and_validate_connection(
            websocket, 12345, room_repository, room_user_repository, user_repository
        )

    assert result == (None, None, None)
    websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)


@pytest.mark.asyncio
async def test_authenticate_and_validate_connection_different_room():
    websocket = AsyncMock(spec=WebSocket)
    websocket.headers.get.return_value = "valid_token"

    user_id = uuid.uuid4()
    room_id = uuid.uuid4()
    different_room_id = uuid.uuid4()

    user = User(id=user_id, uid="123456789", nickname="TestUser")
    room = Room(id=room_id, room_number=12345, host_id=user_id, name="TestRoom")
    room_user = RoomUser(room_id=different_room_id, user_id=user_id)

    room_repository = AsyncMock()
    room_repository.get_by_room_number.return_value = room

    room_user_repository = AsyncMock()
    room_user_repository.get_by_user.return_value = room_user

    user_repository = AsyncMock()
    user_repository.get_by_uuid.return_value = user

    with patch(
        "app.core.room_connection_manager.get_user_id_from_token", return_value=user_id
    ):
        result = await RoomConnectionManager.authenticate_and_validate_connection(
            websocket, 12345, room_repository, room_user_repository, user_repository
        )

    assert result == (None, None, None)
    websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)
