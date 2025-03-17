import pytest
import pytest_asyncio

from app.models.room import Room
from app.models.room_user import RoomUser
from app.models.user import User
from app.repositories.room_user_repository import RoomUserRepository


@pytest_asyncio.fixture
async def test_users(test_db_session) -> list[User]:
    user1 = User(
        uid="100000000",
        nickname="HostUser",
        email="host@example.com",
    )

    user2 = User(
        uid="200000000",
        nickname="TestUser0",
        email="test0@example.com",
    )

    user3 = User(
        uid="300000000",
        nickname="TestUser1",
        email="test1@example.com",
    )

    test_db_session.add(user1)
    test_db_session.add(user2)
    test_db_session.add(user3)

    await test_db_session.commit()
    await test_db_session.refresh(user1)
    await test_db_session.refresh(user2)
    await test_db_session.refresh(user3)

    return [user1, user2, user3]


@pytest_asyncio.fixture
async def test_room(test_db_session, test_users) -> Room:
    room = Room(
        name="Test Room",
        room_number=123,
        max_users=4,
        is_playing=False,
        host_id=test_users[0].id,
    )

    test_db_session.add(room)
    await test_db_session.commit()
    await test_db_session.refresh(room)

    return room


@pytest_asyncio.fixture
async def test_room_users(test_db_session, test_room, test_users) -> list[RoomUser]:
    room_users = []

    for idx, user in enumerate(test_users):
        room_user = RoomUser(
            room_id=test_room.id,
            user_id=user.id,
            is_ready=(idx < 2),
        )
        test_db_session.add(room_user)
        room_users.append(room_user)

    await test_db_session.commit()

    for room_user in room_users:
        await test_db_session.refresh(room_user)

    return room_users


@pytest.mark.asyncio
async def test_get_by_room(test_db_session, test_room, test_room_users):
    repo = RoomUserRepository(test_db_session)
    result = await repo.get_by_room(test_room.id)

    assert len(result) == 3
    assert all(ru.room_id == test_room.id for ru in result)


@pytest.mark.asyncio
async def test_get_by_user(test_db_session, test_users, test_room_users):
    repo = RoomUserRepository(test_db_session)
    result = await repo.get_by_user(test_users[0].id)

    assert result is not None
    assert result.user_id == test_users[0].id
    assert result.is_ready is True

    non_existent_user_id = "00000000-0000-0000-0000-000000000000"
    non_existent_result = await repo.get_by_user(non_existent_user_id)
    assert non_existent_result is None


@pytest.mark.asyncio
async def test_create_and_update_room_user(test_db_session, test_room):
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
    assert created.is_ready is False

    created.is_ready = True
    updated = await repo.update(created)

    assert updated.is_ready is True

    check = await repo.get_by_user(new_user.id)
    assert check is not None
    assert check.is_ready is True


@pytest.mark.asyncio
async def test_delete_by_user(test_db_session, test_users, test_room, test_room_users):
    repo = RoomUserRepository(test_db_session)

    await repo.delete_by_user(test_users[0].id)

    result = await repo.get_by_user(test_users[0].id)
    assert result is None

    result = await repo.get_by_user(test_users[1].id)
    assert result is not None
    assert result.user_id == test_users[1].id
    assert result.room_id == test_room.id
