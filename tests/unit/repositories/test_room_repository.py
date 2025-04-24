import pytest
import pytest_asyncio

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.room import Room
from app.models.room_user import RoomUser
from app.models.user import User
from app.repositories.room_repository import RoomRepository

pytestmark = pytest.mark.skip(reason="모든 테스트 스킵")


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
        room_number=123,
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
        room_number=456,
        max_users=4,
        is_playing=True,
        host_id=test_host.id,
    )
    test_db_session.add(room)
    await test_db_session.commit()
    await test_db_session.refresh(room)
    return room


@pytest.mark.asyncio
async def test_filter_one_room_by_room_number(test_db_session, test_room):
    repo = RoomRepository(test_db_session)
    result = await repo.filter_one_or_raise(room_number=test_room.room_number)
    assert result is not None
    assert result.id == test_room.id
    assert result.name == test_room.name
    assert result.room_number == test_room.room_number
    assert result.host_id == test_room.host_id


@pytest.mark.asyncio
async def test_filter_available_rooms(test_db_session, test_room, test_playing_room):
    repo = RoomRepository(test_db_session)
    results = await repo.filter(is_playing=False)
    assert len(results) == 1
    assert results[0].id == test_room.id
    assert not results[0].is_playing
    for room in results:
        assert room.id != test_playing_room.id


@pytest.mark.asyncio
async def test_nonexistent_room_number(test_db_session):
    repo = RoomRepository(test_db_session)
    with pytest.raises(MCRDomainError) as exc_info:
        await repo.filter_one_or_raise(room_number=99999)
    assert exc_info.value.code == DomainErrorCode.ROOM_NOT_FOUND


@pytest.mark.asyncio
async def test_create_room(test_db_session, test_host):
    room = Room(
        name="New Room",
        max_users=4,
        is_playing=False,
        host_id=test_host.id,
    )
    repo = RoomRepository(test_db_session)
    created_room = await repo.create_with_room_number(room)
    assert created_room.id is not None
    assert created_room.name == room.name
    assert created_room.room_number is not None
    result = await repo.filter_one_or_raise(room_number=created_room.room_number)
    assert result is not None
    assert result.id == created_room.id


@pytest.mark.asyncio
async def test_get_available_rooms_with_users(test_db_session, test_host):
    user1 = User(
        uid="100000001",
        nickname="TestUser1",
        email="test1@example.com",
    )
    user2 = User(
        uid="100000002",
        nickname="TestUser2",
        email="test2@example.com",
    )
    test_db_session.add(user1)
    test_db_session.add(user2)
    await test_db_session.commit()
    await test_db_session.refresh(user1)
    await test_db_session.refresh(user2)

    room1 = Room(
        name="Available Room",
        room_number=123,
        max_users=4,
        is_playing=False,
        host_id=test_host.id,
    )
    room2 = Room(
        name="Playing Room",
        room_number=456,
        max_users=4,
        is_playing=True,
        host_id=test_host.id,
    )
    test_db_session.add(room1)
    test_db_session.add(room2)
    await test_db_session.commit()
    await test_db_session.refresh(room1)
    await test_db_session.refresh(room2)

    room_user1 = RoomUser(
        room_id=room1.id,
        user_id=user1.id,
        user_uid=user1.uid,
        user_nickname=user1.nickname,
        is_ready=True,
        slot_index=0,
    )
    room_user2 = RoomUser(
        room_id=room1.id,
        user_id=user2.id,
        user_uid=user2.uid,
        user_nickname=user2.nickname,
        is_ready=False,
        slot_index=1,
    )
    room_user3 = RoomUser(
        room_id=room2.id,
        user_id=test_host.id,
        user_uid=test_host.uid,
        user_nickname=test_host.nickname,
        is_ready=True,
        slot_index=2,
    )
    test_db_session.add(room_user1)
    test_db_session.add(room_user2)
    test_db_session.add(room_user3)
    await test_db_session.commit()

    repo = RoomRepository(test_db_session)
    results = await repo.get_available_rooms_with_users()
    assert len(results) == 1
    room, room_users = results[0]
    assert room.id == room1.id
    assert room.name == "Available Room"
    assert room.is_playing is False
    assert len(room_users) == 2
    assert any(ru.user_id == user1.id for ru in room_users)
    assert any(ru.user_id == user2.id for ru in room_users)
