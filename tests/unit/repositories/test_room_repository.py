import pytest
import pytest_asyncio

from app.models.room import Room
from app.models.user import User
from app.repositories.room_repository import RoomRepository


@pytest_asyncio.fixture
async def test_host(test_db_session) -> User:
    host = User(
        uid="123456789",
        nickname="HostUser",
        email="host@example.com",
    )

    test_db_session.add(host)
    await test_db_session.commit()
    await test_db_session.refresh(host)

    return host


@pytest_asyncio.fixture
async def test_room(test_db_session, test_host) -> Room:
    room = Room(
        name="Test Room",
        room_number="TEST123",
        max_users=4,
        is_playing=False,
        host_id=test_host.id,
    )

    test_db_session.add(room)
    await test_db_session.commit()
    await test_db_session.refresh(room)

    return room


@pytest_asyncio.fixture
async def test_playing_room(test_db_session, test_host) -> Room:
    room = Room(
        name="Playing Room",
        room_number="PLAY456",
        max_users=4,
        is_playing=True,
        host_id=test_host.id,
    )

    test_db_session.add(room)
    await test_db_session.commit()
    await test_db_session.refresh(room)

    return room


@pytest.mark.asyncio
async def test_get_by_uuid(test_db_session, test_room):
    repo = RoomRepository(test_db_session)
    result = await repo.get_by_uuid(test_room.id)

    assert result is not None
    assert result.id == test_room.id
    assert result.name == test_room.name
    assert result.room_number == test_room.room_number
    assert result.host_id == test_room.host_id


@pytest.mark.asyncio
async def test_get_by_room_number(test_db_session, test_room):
    repo = RoomRepository(test_db_session)
    result = await repo.get_by_room_number(test_room.room_number)

    assert result is not None
    assert result.id == test_room.id
    assert result.name == test_room.name
    assert result.room_number == test_room.room_number


@pytest.mark.asyncio
async def test_get_available_rooms(test_db_session, test_room, test_playing_room):
    repo = RoomRepository(test_db_session)
    results = await repo.get_available_rooms()

    assert len(results) == 1
    assert results[0].id == test_room.id
    assert not results[0].is_playing

    for room in results:
        assert room.id != test_playing_room.id


@pytest.mark.asyncio
async def test_create_room(test_db_session, test_host):
    room = Room(
        name="New Room",
        room_number="NEW789",
        max_users=4,
        is_playing=False,
        host_id=test_host.id,
    )

    repo = RoomRepository(test_db_session)
    created_room = await repo.create(room)

    assert created_room.id is not None
    assert created_room.name == room.name
    assert created_room.room_number == room.room_number

    result = await repo.get_by_room_number(room.room_number)
    assert result is not None
    assert result.id == created_room.id


@pytest.mark.asyncio
async def test_update_room(test_db_session, test_room):
    test_room.name = "Updated Room"
    test_room.max_users = 3

    repo = RoomRepository(test_db_session)
    updated_room = await repo.update(test_room)

    assert updated_room.name == "Updated Room"
    assert updated_room.max_users == 3

    result = await repo.get_by_uuid(test_room.id)
    assert result is not None
    assert result.name == "Updated Room"
    assert result.max_users == 3


@pytest.mark.asyncio
async def test_delete_room(test_db_session, test_room):
    repo = RoomRepository(test_db_session)
    await repo.delete(test_room.id)

    result = await repo.get_by_uuid(test_room.id)
    assert result is None

    result = await repo.get_by_room_number(test_room.room_number)
    assert result is None
