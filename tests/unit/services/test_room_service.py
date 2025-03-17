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

    room_user = RoomUser(room_id=room_id, user_id=user_id, is_ready=True)
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
    assert "current_room_id" in exc_info.value.details


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
async def test_join_room_host(mock_room_service, user_id, room_id):
    user = User(id=user_id, uid="123456789", nickname="HostUser")
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        max_users=4,
        is_playing=False,
        host_id=user_id,
    )
    room_user = RoomUser(room_id=room_id, user_id=user_id, is_ready=True)

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_repository.get_by_uuid.return_value = room
    mock_room_service.room_user_repository.get_by_room.return_value = []
    mock_room_service.room_user_repository.get_by_user.return_value = None
    mock_room_service.room_user_repository.create.return_value = room_user

    result = await mock_room_service.join_room(user_id, room_id)

    assert result.room_id == room_id
    assert result.user_id == user_id
    assert result.is_ready is True

    mock_room_service.session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_join_room_user_not_found(mock_room_service, user_id, room_id):
    mock_room_service.user_repository.get_by_uuid.return_value = None

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.join_room(user_id, room_id)

    assert exc_info.value.code == DomainErrorCode.USER_NOT_FOUND


@pytest.mark.asyncio
async def test_join_room_not_found(mock_room_service, user_id, room_id):
    user = User(id=user_id, uid="123456789", nickname="TestUser")

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_repository.get_by_uuid.return_value = None

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.join_room(user_id, room_id)

    assert exc_info.value.code == DomainErrorCode.ROOM_NOT_FOUND


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
    assert "max_users" in exc_info.value.details


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
    assert "current_room_id" in exc_info.value.details


@pytest.mark.asyncio
async def test_toggle_ready_success(mock_room_service, user_id, room_id):
    user = User(id=user_id, uid="123456789", nickname="TestUser")
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        max_users=4,
        is_playing=False,
        host_id=uuid.uuid4(),
    )

    room_user = RoomUser(room_id=room_id, user_id=user_id, is_ready=False)

    updated_room_user = RoomUser(room_id=room_id, user_id=user_id, is_ready=True)

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_repository.get_by_uuid.return_value = room
    mock_room_service.room_user_repository.get_by_user.return_value = room_user
    mock_room_service.room_user_repository.update.return_value = updated_room_user

    result = await mock_room_service.toggle_ready(user_id, room_id)

    assert result.is_ready is True
    assert result.room_id == room_id
    assert result.user_id == user_id

    mock_room_service.session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_toggle_ready_from_ready_to_unready(mock_room_service, user_id, room_id):
    host_id = uuid.uuid4()
    user = User(id=user_id, uid="123456789", nickname="TestUser")
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        max_users=4,
        is_playing=False,
        host_id=host_id,
    )

    room_user = RoomUser(room_id=room_id, user_id=user_id, is_ready=True)

    updated_room_user = RoomUser(room_id=room_id, user_id=user_id, is_ready=False)

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_repository.get_by_uuid.return_value = room
    mock_room_service.room_user_repository.get_by_user.return_value = room_user
    mock_room_service.room_user_repository.update.return_value = updated_room_user

    result = await mock_room_service.toggle_ready(user_id, room_id)

    assert result.is_ready is False


@pytest.mark.asyncio
async def test_toggle_ready_host_error(mock_room_service, user_id, room_id):
    user = User(id=user_id, uid="123456789", nickname="HostUser")
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        max_users=4,
        is_playing=False,
        host_id=user_id,
    )

    room_user = RoomUser(room_id=room_id, user_id=user_id, is_ready=True)

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_repository.get_by_uuid.return_value = room
    mock_room_service.room_user_repository.get_by_user.return_value = room_user

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.toggle_ready(user_id, room_id)

    assert exc_info.value.code == DomainErrorCode.HOST_CANNOT_READY


@pytest.mark.asyncio
async def test_toggle_ready_room_playing_error(mock_room_service, user_id, room_id):
    host_id = uuid.uuid4()
    user = User(id=user_id, uid="123456789", nickname="TestUser")
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        max_users=4,
        is_playing=True,
        host_id=host_id,
    )

    room_user = RoomUser(room_id=room_id, user_id=user_id, is_ready=True)

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_repository.get_by_uuid.return_value = room
    mock_room_service.room_user_repository.get_by_user.return_value = room_user

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.toggle_ready(user_id, room_id)

    assert exc_info.value.code == DomainErrorCode.ROOM_ALREADY_PLAYING


@pytest.mark.asyncio
async def test_toggle_ready_user_not_in_room(mock_room_service, user_id, room_id):
    user = User(id=user_id, uid="123456789", nickname="TestUser")
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        max_users=4,
        is_playing=False,
        host_id=uuid.uuid4(),
    )

    other_room_id = uuid.uuid4()
    room_user = RoomUser(room_id=other_room_id, user_id=user_id, is_ready=False)

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_repository.get_by_uuid.return_value = room
    mock_room_service.room_user_repository.get_by_user.return_value = room_user

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.toggle_ready(user_id, room_id)

    assert exc_info.value.code == DomainErrorCode.USER_NOT_IN_ROOM


@pytest.mark.asyncio
async def test_leave_room_only_user(mock_room_service, user_id, room_id):
    user = User(id=user_id, uid="123456789", nickname="TestUser")
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        max_users=4,
        is_playing=False,
        host_id=user_id,
    )
    room_user = RoomUser(room_id=room_id, user_id=user_id, is_ready=True)

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_user_repository.get_by_user.return_value = room_user
    mock_room_service.room_repository.get_by_uuid.return_value = room

    mock_room_service.room_user_repository.get_by_room.return_value = []
    mock_room_service.room_repository.delete.return_value = None

    await mock_room_service.leave_room(user_id)

    mock_room_service.room_repository.delete.assert_awaited_once_with(room_id)


@pytest.mark.asyncio
async def test_leave_room_host_with_others(mock_room_service, user_id, room_id):
    host_id = user_id
    other_user_id = uuid.uuid4()

    user = User(id=host_id, uid="123456789", nickname="HostUser")
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        max_users=4,
        is_playing=False,
        host_id=host_id,
    )
    host_room_user = RoomUser(room_id=room_id, user_id=host_id, is_ready=True)
    other_room_user = RoomUser(room_id=room_id, user_id=other_user_id, is_ready=False)

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_user_repository.get_by_user.return_value = host_room_user
    mock_room_service.room_repository.get_by_uuid.return_value = room
    mock_room_service.room_user_repository.get_by_room.return_value = [other_room_user]

    await mock_room_service.leave_room(host_id)

    assert room.host_id == other_user_id
    assert other_room_user.is_ready is True


@pytest.mark.asyncio
async def test_leave_room_non_host(mock_room_service, user_id, room_id):
    host_id = uuid.uuid4()
    non_host_id = user_id

    user = User(id=non_host_id, uid="123456789", nickname="RegularUser")
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        max_users=4,
        is_playing=False,
        host_id=host_id,
    )
    host_room_user = RoomUser(room_id=room_id, user_id=host_id, is_ready=True)
    non_host_room_user = RoomUser(room_id=room_id, user_id=non_host_id, is_ready=False)

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_user_repository.get_by_user.return_value = non_host_room_user
    mock_room_service.room_repository.get_by_uuid.return_value = room
    mock_room_service.room_user_repository.get_by_room.return_value = [host_room_user]

    original_delete_by_user = mock_room_service.room_user_repository.delete_by_user
    delete_calls = []

    async def mock_delete_by_user(user_id):
        delete_calls.append(user_id)
        await original_delete_by_user(user_id)

    mock_room_service.room_user_repository.delete_by_user = mock_delete_by_user

    await mock_room_service.leave_room(non_host_id)

    assert non_host_id in delete_calls
    assert room.host_id == host_id


@pytest.mark.asyncio
async def test_leave_room_playing_error(mock_room_service, user_id, room_id):
    user = User(id=user_id, uid="123456789", nickname="TestUser")
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        max_users=4,
        is_playing=True,
        host_id=uuid.uuid4(),
    )
    room_user = RoomUser(room_id=room_id, user_id=user_id, is_ready=True)

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_user_repository.get_by_user.return_value = room_user
    mock_room_service.room_repository.get_by_uuid.return_value = room

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.leave_room(user_id)

    assert exc_info.value.code == DomainErrorCode.ROOM_ALREADY_PLAYING
    assert str(room_id) in exc_info.value.details["room_id"]


@pytest.mark.asyncio
async def test_leave_room_user_not_found(mock_room_service, user_id):
    mock_room_service.user_repository.get_by_uuid.return_value = None

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.leave_room(user_id)

    assert exc_info.value.code == DomainErrorCode.USER_NOT_FOUND
    assert str(user_id) in exc_info.value.details["user_id"]


@pytest.mark.asyncio
async def test_leave_room_user_not_in_room(mock_room_service, user_id):
    user = User(id=user_id, uid="123456789", nickname="TestUser")

    mock_room_service.user_repository.get_by_uuid.return_value = user
    mock_room_service.room_user_repository.get_by_user.return_value = None

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.leave_room(user_id)

    assert exc_info.value.code == DomainErrorCode.USER_NOT_IN_ROOM
    assert str(user_id) in exc_info.value.details["user_id"]
