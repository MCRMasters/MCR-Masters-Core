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
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        max_users=4,
        is_playing=False,
        host_id=user_id,
    )
    room_user = RoomUser(room_id=room_id, user_id=user_id, is_ready=True)

    mock_room_service.user_repository.get_by_uuid.return_value = host
    mock_room_service.room_user_repository.get_by_user.return_value = None
    mock_room_service.room_repository.create.return_value = room
    mock_room_service.room_user_repository.create.return_value = room_user

    created_room = await mock_room_service.create_room(user_id)

    assert created_room.id == room_id
    assert created_room.name == "엄숙한 패황전"
    assert created_room.max_users == 4
    assert created_room.is_playing is False
    assert created_room.host_id == user_id


@pytest.mark.asyncio
async def test_create_room_user_not_found(mock_room_service, user_id):
    mock_room_service.user_repository.get_by_uuid.return_value = None

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.create_room(user_id)

    assert exc_info.value.code == DomainErrorCode.USER_NOT_FOUND


@pytest.mark.asyncio
async def test_create_room_user_already_in_room(mock_room_service, user_id, room_id):
    host = User(id=user_id, uid="123456789", nickname="HostUser")
    existing_room_user = RoomUser(room_id=room_id, user_id=user_id, is_ready=True)

    mock_room_service.user_repository.get_by_uuid.return_value = host
    mock_room_service.room_user_repository.get_by_user.return_value = existing_room_user

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_room_service.create_room(user_id)

    assert exc_info.value.code == DomainErrorCode.USER_ALREADY_IN_ROOM
