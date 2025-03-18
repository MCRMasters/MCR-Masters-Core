import uuid

import pytest
import pytest_asyncio

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.room import Room
from app.models.room_user import RoomUser
from app.models.user import User
from app.services.room_service import RoomService


@pytest.fixture
def room_id():
    return uuid.uuid4()


@pytest_asyncio.fixture
async def mock_room_service(mocker):
    session = mocker.AsyncMock()
    room_repository = mocker.AsyncMock()
    room_user_repository = mocker.AsyncMock()
    user_repository = mocker.AsyncMock()

    service = RoomService(
        session=session,
        room_repository=room_repository,
        room_user_repository=room_user_repository,
        user_repository=user_repository,
    )

    mocker.patch.object(
        service,
        "_generate_random_room_name",
        return_value="엄숙한 패황전",
    )

    return service


@pytest.mark.asyncio
async def test_create_room_success(mock_room_service, user_id, room_id):
    host = User(id=user_id, uid="123456789", nickname="HostUser")
    mock_room_service.user_repository.get_by_uuid.return_value = host

    mock_room_service.room_user_repository.get_by_user.return_value = None

    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        max_users=4,
        is_playing=False,
        host_id=user_id,
    )
    mock_room_service.room_repository.create_with_room_number.return_value = room

    mock_room_service.room_repository.get_by_uuid.return_value = room

    mock_room_service.room_user_repository.get_by_room.return_value = []

    room_user = RoomUser(room_id=room_id, user_id=user_id, is_ready=False)
    mock_room_service.room_user_repository.create.return_value = room_user

    created_room = await mock_room_service.create_room(user_id)

    assert created_room.id == room_id
    assert created_room.name == "엄숙한 패황전"
    assert created_room.max_users == 4
    assert created_room.is_playing is False
    assert created_room.host_id == user_id

    mock_room_service.session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_room_user_not_found(mock_room_service, user_id):
    mock_room_service.user_repository.get_by_uuid.return_value = None

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.create_room(user_id)

    assert exc_info.value.code == DomainErrorCode.USER_NOT_FOUND
    assert str(user_id) in exc_info.value.message


@pytest.mark.asyncio
async def test_create_room_user_already_in_room(mock_room_service, user_id):
    host = User(id=user_id, uid="123456789", nickname="HostUser")
    existing_room_id = uuid.uuid4()
    existing_room_user = RoomUser(
        room_id=existing_room_id,
        user_id=user_id,
        is_ready=True,
    )

    mock_room_service.user_repository.get_by_uuid.return_value = host
    mock_room_service.room_user_repository.get_by_user.return_value = existing_room_user

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.create_room(user_id)

    assert exc_info.value.code == DomainErrorCode.USER_ALREADY_IN_ROOM
    assert str(user_id) in exc_info.value.message
    assert str(existing_room_id) in exc_info.value.details["current_room_id"]


@pytest.mark.asyncio
async def test_join_room_success(mock_room_service, user_id, room_id):
    user = User(id=user_id, uid="123456789", nickname="TestUser")
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        max_users=4,
        is_playing=False,
        host_id=uuid.uuid4(),
    )
    room_user = RoomUser(room_id=room_id, user_id=user_id, is_ready=False)

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_repository.get_by_uuid.return_value = room
    mock_room_service.room_user_repository.get_by_room.return_value = []
    mock_room_service.room_user_repository.get_by_user.return_value = None
    mock_room_service.room_user_repository.create.return_value = room_user

    result = await mock_room_service.join_room(user_id, room_id)

    assert result.room_id == room_id
    assert result.user_id == user_id
    assert result.is_ready is False

    mock_room_service.session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_join_room_user_not_found(mock_room_service, user_id, room_id):
    mock_room_service.user_repository.get_by_uuid.return_value = None

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.join_room(user_id, room_id)

    assert exc_info.value.code == DomainErrorCode.USER_NOT_FOUND
    assert str(user_id) in exc_info.value.message


@pytest.mark.asyncio
async def test_join_room_not_found(mock_room_service, user_id, room_id):
    user = User(id=user_id, uid="123456789", nickname="TestUser")

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_repository.get_by_uuid.return_value = None

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.join_room(user_id, room_id)

    assert exc_info.value.code == DomainErrorCode.ROOM_NOT_FOUND
    assert str(room_id) in exc_info.value.message


@pytest.mark.asyncio
async def test_join_room_is_playing(mock_room_service, user_id, room_id):
    user = User(id=user_id, uid="123456789", nickname="TestUser")
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        max_users=4,
        is_playing=True,
        host_id=uuid.uuid4(),
    )

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_repository.get_by_uuid.return_value = room

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.join_room(user_id, room_id)

    assert exc_info.value.code == DomainErrorCode.ROOM_ALREADY_PLAYING
    assert str(room_id) in exc_info.value.message


@pytest.mark.asyncio
async def test_join_room_is_full(mock_room_service, user_id, room_id):
    user = User(id=user_id, uid="123456789", nickname="TestUser")
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        max_users=4,
        is_playing=False,
        host_id=uuid.uuid4(),
    )

    room_users = [
        RoomUser(room_id=room_id, user_id=uuid.uuid4()),
        RoomUser(room_id=room_id, user_id=uuid.uuid4()),
        RoomUser(room_id=room_id, user_id=uuid.uuid4()),
        RoomUser(room_id=room_id, user_id=uuid.uuid4()),
    ]

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_repository.get_by_uuid.return_value = room
    mock_room_service.room_user_repository.get_by_room.return_value = room_users
    mock_room_service.room_user_repository.get_by_user.return_value = None

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.join_room(user_id, room_id)

    assert exc_info.value.code == DomainErrorCode.ROOM_IS_FULL
    assert str(room_id) in exc_info.value.message
    assert exc_info.value.details["max_users"] == 4


@pytest.mark.asyncio
async def test_join_room_already_in_room(mock_room_service, user_id, room_id):
    user = User(id=user_id, uid="123456789", nickname="TestUser")
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        max_users=4,
        is_playing=False,
        host_id=uuid.uuid4(),
    )
    existing_room_id = uuid.uuid4()
    existing_room_user = RoomUser(
        room_id=existing_room_id,
        user_id=user_id,
        is_ready=True,
    )

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_repository.get_by_uuid.return_value = room
    mock_room_service.room_user_repository.get_by_room.return_value = []
    mock_room_service.room_user_repository.get_by_user.return_value = existing_room_user

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.join_room(user_id, room_id)

    assert exc_info.value.code == DomainErrorCode.USER_ALREADY_IN_ROOM
    assert str(user_id) in exc_info.value.message
    assert str(existing_room_id) in exc_info.value.details["current_room_id"]


@pytest.mark.asyncio
async def test_get_available_rooms(mock_room_service, user_id, room_id):
    user1 = User(id=user_id, uid="123456789", nickname="HostUser")
    user2 = User(id=uuid.uuid4(), uid="987654321", nickname="GuestUser")

    room = Room(
        id=room_id,
        name="Test Room",
        room_number=123,
        max_users=4,
        is_playing=False,
        host_id=user_id,
    )

    room_user1 = RoomUser(room_id=room_id, user_id=user_id, is_ready=True)
    room_user2 = RoomUser(room_id=room_id, user_id=user2.id, is_ready=False)

    mock_room_service.room_repository.get_available_rooms_with_users.return_value = [
        (room, [room_user1, room_user2])
    ]

    mock_room_service.user_repository.get_by_uuid.side_effect = lambda id: {
        user_id: user1,
        user2.id: user2,
    }.get(id)

    result = await mock_room_service.get_available_rooms()

    assert len(result) == 1
    assert result[0].name == "Test Room"
    assert result[0].room_number == 123
    assert result[0].max_users == 4
    assert result[0].current_users == 2
    assert result[0].host_nickname == "HostUser"

    assert len(result[0].users) == 2

    host_user = next((u for u in result[0].users if u.nickname == "HostUser"), None)
    assert host_user is not None
    assert host_user.is_ready is True

    guest_user = next((u for u in result[0].users if u.nickname == "GuestUser"), None)
    assert guest_user is not None
    assert guest_user.is_ready is False
