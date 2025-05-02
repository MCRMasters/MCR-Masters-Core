import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import WebSocket, status

from app.core.error import DomainErrorCode, MCRDomainError
from app.core.room_connection_manager import RoomConnectionManager
from app.models.room import Room
from app.models.room_user import RoomUser
from app.models.user import User

# TODO
pytestmark = pytest.mark.skip(reason="모든 테스트 스킵")


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
    room_repository.filter_one_or_raise.return_value = room

    room_user_repository = AsyncMock()
    room_user_repository.filter_one_or_raise.return_value = room_user

    user_repository = AsyncMock()
    user_repository.filter_one_or_raise.return_value = user

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

    assert result[0] == user_id  # user_id 체크
    assert result[1] == room_id  # room_id 체크
    assert result[2].id == user.id  # user 객체의 id 체크
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
    user_repository.filter_one_or_raise.side_effect = MCRDomainError(
        code=DomainErrorCode.USER_NOT_FOUND, message=f"User with ID {user_id} not found"
    )

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
    room_repository.filter_one_or_raise.side_effect = MCRDomainError(
        code=DomainErrorCode.ROOM_NOT_FOUND, message="Room not found"
    )

    room_user_repository = AsyncMock()

    user_repository = AsyncMock()
    user_repository.filter_one_or_raise.return_value = user

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
    room_repository.filter_one_or_raise.return_value = room

    room_user_repository = AsyncMock()
    room_user_repository.filter_one_or_raise.side_effect = MCRDomainError(
        code=DomainErrorCode.USER_NOT_IN_ROOM, message="User not in the specified room"
    )

    user_repository = AsyncMock()
    user_repository.filter_one_or_raise.return_value = user

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
    user = User(id=user_id, uid="123456789", nickname="TestUser")
    room = Room(id=room_id, room_number=12345, host_id=user_id, name="TestRoom")

    room_repository = AsyncMock()
    room_repository.filter_one_or_raise.return_value = room

    room_user_repository = AsyncMock()
    room_user_repository.filter_one_or_raise.side_effect = MCRDomainError(
        code=DomainErrorCode.USER_NOT_IN_ROOM, message="User is in a different room"
    )

    user_repository = AsyncMock()
    user_repository.filter_one_or_raise.return_value = user

    with patch(
        "app.core.room_connection_manager.get_user_id_from_token", return_value=user_id
    ):
        result = await RoomConnectionManager.authenticate_and_validate_connection(
            websocket, 12345, room_repository, room_user_repository, user_repository
        )

    assert result == (None, None, None)
    websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)
