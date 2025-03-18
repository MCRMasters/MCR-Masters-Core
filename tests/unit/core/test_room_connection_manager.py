import uuid
from unittest.mock import AsyncMock

import pytest

from app.core.room_connection_manager import RoomConnectionManager


@pytest.mark.asyncio
async def test_connect():
    manager = RoomConnectionManager()
    websocket = AsyncMock()
    room_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await manager.connect(websocket, room_id, user_id)

    websocket.accept.assert_called_once()
    assert user_id in manager.active_connections[room_id]
    assert manager.user_rooms[user_id] == room_id


@pytest.mark.asyncio
async def test_disconnect():
    manager = RoomConnectionManager()
    websocket = AsyncMock()
    room_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await manager.connect(websocket, room_id, user_id)
    manager.disconnect(room_id, user_id)

    assert not manager.active_connections.get(room_id)
    assert user_id not in manager.user_rooms


@pytest.mark.asyncio
async def test_broadcast():
    manager = RoomConnectionManager()
    websocket1 = AsyncMock()
    websocket2 = AsyncMock()
    room_id = uuid.uuid4()
    user_id1 = uuid.uuid4()
    user_id2 = uuid.uuid4()

    await manager.connect(websocket1, room_id, user_id1)
    await manager.connect(websocket2, room_id, user_id2)

    message = {"status": "success", "action": "test"}
    await manager.broadcast(message, room_id)

    websocket1.send_json.assert_called_once_with(message)
    websocket2.send_json.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_broadcast_with_exclude():
    manager = RoomConnectionManager()
    websocket1 = AsyncMock()
    websocket2 = AsyncMock()
    room_id = uuid.uuid4()
    user_id1 = uuid.uuid4()
    user_id2 = uuid.uuid4()

    await manager.connect(websocket1, room_id, user_id1)
    await manager.connect(websocket2, room_id, user_id2)

    message = {"status": "success", "action": "test"}
    await manager.broadcast(message, room_id, exclude_user_id=user_id1)

    websocket1.send_json.assert_not_called()
    websocket2.send_json.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_personal_message():
    manager = RoomConnectionManager()
    websocket1 = AsyncMock()
    websocket2 = AsyncMock()
    room_id = uuid.uuid4()
    user_id1 = uuid.uuid4()
    user_id2 = uuid.uuid4()

    await manager.connect(websocket1, room_id, user_id1)
    await manager.connect(websocket2, room_id, user_id2)

    message = {"status": "success", "action": "test"}
    await manager.send_personal_message(message, room_id, user_id1)

    websocket1.send_json.assert_called_once_with(message)
    websocket2.send_json.assert_not_called()


def test_get_room_users():
    manager = RoomConnectionManager()
    room_id = uuid.uuid4()
    user_id1 = uuid.uuid4()
    user_id2 = uuid.uuid4()

    manager.active_connections[room_id] = {user_id1: AsyncMock(), user_id2: AsyncMock()}

    users = manager.get_room_users(room_id)

    assert len(users) == 2
    assert user_id1 in users
    assert user_id2 in users


def test_is_user_in_room():
    manager = RoomConnectionManager()
    room_id = uuid.uuid4()
    user_id = uuid.uuid4()

    manager.active_connections[room_id] = {user_id: AsyncMock()}

    assert manager.is_user_in_room(room_id, user_id) is True
    assert manager.is_user_in_room(room_id, uuid.uuid4()) is False
    assert manager.is_user_in_room(uuid.uuid4(), user_id) is False
