import pytest
import pytest_asyncio

from app.models.room import Room
from app.models.room_user import RoomUser
from app.models.user import User
from app.repositories.room_user_repository import RoomUserRepository


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
async def test_users(test_db_session) -> list[User]:
    user1 = User(
        uid="200000000",
        nickname="TestUser0",
        email="test0@example.com",
    )

    user2 = User(
        uid="300000000",
        nickname="TestUser1",
        email="test1@example.com",
    )

    test_db_session.add(user1)
    test_db_session.add(user2)

    await test_db_session.commit()
    await test_db_session.refresh(user1)
    await test_db_session.refresh(user2)

    return [user1, user2]


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
async def test_room_users(
    test_db_session,
    test_room,
    test_host,
    test_users,
) -> list[RoomUser]:
    host_room_user = RoomUser(
        room_id=test_room.id,
        user_id=test_host.id,
        is_ready=True,
    )

    room_user1 = RoomUser(
        room_id=test_room.id,
        user_id=test_users[0].id,
        is_ready=True,
    )

    room_user2 = RoomUser(
        room_id=test_room.id,
        user_id=test_users[1].id,
        is_ready=False,
    )

    test_db_session.add(host_room_user)
    test_db_session.add(room_user1)
    test_db_session.add(room_user2)

    await test_db_session.commit()
    await test_db_session.refresh(host_room_user)
    await test_db_session.refresh(room_user1)
    await test_db_session.refresh(room_user2)

    return [host_room_user, room_user1, room_user2]


@pytest.mark.asyncio
async def test_get_by_room(test_db_session, test_room, test_room_users):
    repo = RoomUserRepository(test_db_session)
    result = await repo.get_by_room(test_room.id)

    assert len(result) == 3
    assert all(ru.room_id == test_room.id for ru in result)


@pytest.mark.asyncio
async def test_get_by_user(test_db_session, test_host, test_room_users):
    repo = RoomUserRepository(test_db_session)
    result = await repo.get_by_user(test_host.id)

    assert result is not None
    assert result.user_id == test_host.id
    assert result.room_id == test_room_users[0].room_id
    assert result.is_ready is True


@pytest.mark.asyncio
async def test_get_by_user_not_found(test_db_session):
    from uuid import uuid4

    non_existent_id = uuid4()

    repo = RoomUserRepository(test_db_session)
    result = await repo.get_by_user(non_existent_id)

    assert result is None


@pytest.mark.asyncio
async def test_create_room_user(test_db_session, test_room):
    new_user = User(
        uid="987654321",
        nickname="NewUser",
        email="new@example.com",
    )
    test_db_session.add(new_user)
    await test_db_session.commit()
    await test_db_session.refresh(new_user)

    room_user = RoomUser(
        room_id=test_room.id,
        user_id=new_user.id,
        is_ready=False,
    )

    repo = RoomUserRepository(test_db_session)
    created = await repo.create(room_user)

    assert created.id is not None
    assert created.room_id == test_room.id
    assert created.user_id == new_user.id

    fetched = await repo.get_by_user(new_user.id)
    assert fetched is not None
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_update_room_user(test_db_session, test_users, test_room_users):
    repo = RoomUserRepository(test_db_session)

    room_user = await repo.get_by_user(test_users[1].id)
    assert room_user is not None
    assert room_user.is_ready is False

    room_user.is_ready = True
    updated = await repo.update(room_user)

    assert updated.is_ready is True

    checked = await repo.get_by_user(test_users[1].id)
    assert checked.is_ready is True


@pytest.mark.asyncio
async def test_delete_room_user(test_db_session, test_users, test_room_users):
    repo = RoomUserRepository(test_db_session)

    user_id = test_users[0].id
    before_delete = await repo.get_by_user(user_id)
    assert before_delete is not None

    await repo.delete(before_delete.id)

    after_delete = await repo.get_by_user(user_id)
    assert after_delete is None
