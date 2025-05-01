import uuid

import pytest
import pytest_asyncio

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.room import Room
from app.models.room_user import RoomUser
from app.models.user import User
from app.services.room_service import RoomService

pytestmark = pytest.mark.skip(reason="모든 테스트 스킵")


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


class TestRoomServiceCreateRoom:
    @pytest.mark.asyncio
    async def test_create_room_success(self, mock_room_service, user_id, room_id):
        host = User(id=user_id, uid="123456789", nickname="HostUser")
        mock_room_service.user_repository.filter_one_or_raise.return_value = host
        mock_room_service.room_user_repository.filter_one.return_value = None

        room = Room(
            id=room_id,
            name="엄숙한 패황전",
            max_users=4,
            is_playing=False,
            host_id=user_id,
        )
        mock_room_service.room_repository.create_with_room_number.return_value = room
        mock_room_service.room_repository.filter_one_or_raise.return_value = room
        mock_room_service.room_user_repository.filter.return_value = []

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
    async def test_create_room_user_not_found(self, mock_room_service, user_id):
        mock_room_service.user_repository.filter_one_or_raise.side_effect = (
            MCRDomainError(
                code=DomainErrorCode.USER_NOT_FOUND,
                message=f"User with ID {user_id} not found",
                details={"user_id": str(user_id)},
            )
        )

        with pytest.raises(MCRDomainError) as exc_info:
            await mock_room_service.create_room(user_id)

        assert exc_info.value.code == DomainErrorCode.USER_NOT_FOUND
        assert str(user_id) in exc_info.value.message

    @pytest.mark.asyncio
    async def test_create_room_user_already_in_room(self, mock_room_service, user_id):
        host = User(id=user_id, uid="123456789", nickname="HostUser")
        existing_room_id = uuid.uuid4()
        existing_room_user = RoomUser(
            room_id=existing_room_id,
            user_id=user_id,
            is_ready=True,
        )

        mock_room_service.user_repository.filter_one_or_raise.return_value = host
        mock_room_service.room_user_repository.filter_one.return_value = (
            existing_room_user
        )

        with pytest.raises(MCRDomainError) as exc_info:
            await mock_room_service.create_room(user_id)

        assert exc_info.value.code == DomainErrorCode.USER_ALREADY_IN_ROOM
        assert str(user_id) in exc_info.value.message
        assert str(existing_room_id) in exc_info.value.details["current_room_id"]


class TestRoomServiceJoinRoom:
    @pytest.mark.asyncio
    async def test_join_room_success(self, mock_room_service, user_id, room_id):
        user = User(id=user_id, uid="123456789", nickname="TestUser")
        room = Room(
            id=room_id,
            name="엄숙한 패황전",
            max_users=4,
            is_playing=False,
            host_id=uuid.uuid4(),
        )
        room_user = RoomUser(room_id=room_id, user_id=user_id, is_ready=False)

        mock_room_service.user_repository.filter_one_or_raise.return_value = user
        mock_room_service.room_repository.filter_one_or_raise.return_value = room
        mock_room_service.room_user_repository.filter.return_value = []
        mock_room_service.room_user_repository.filter_one.return_value = None
        mock_room_service.room_user_repository.create.return_value = room_user

        result = await mock_room_service.join_room(user_id, room_id)

        assert result.room_id == room_id
        assert result.user_id == user_id
        assert result.is_ready is False
        mock_room_service.session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_join_room_is_playing(self, mock_room_service, user_id, room_id):
        user = User(id=user_id, uid="123456789", nickname="TestUser")
        room = Room(
            id=room_id,
            name="엄숙한 패황전",
            max_users=4,
            is_playing=True,
            host_id=uuid.uuid4(),
        )

        mock_room_service.user_repository.filter_one_or_raise.return_value = user
        mock_room_service.room_repository.filter_one_or_raise.return_value = room

        with pytest.raises(MCRDomainError) as exc_info:
            await mock_room_service.join_room(user_id, room_id)

        assert exc_info.value.code == DomainErrorCode.ROOM_ALREADY_PLAYING
        assert str(room_id) in exc_info.value.message

    @pytest.mark.asyncio
    async def test_join_room_is_full(self, mock_room_service, user_id, room_id):
        user = User(id=user_id, uid="123456789", nickname="TestUser")
        room = Room(
            id=room_id,
            name="엄숙한 패황전",
            max_users=4,
            is_playing=False,
            host_id=uuid.uuid4(),
        )

        room_users = [RoomUser(room_id=room_id, user_id=uuid.uuid4()) for _ in range(4)]

        mock_room_service.user_repository.filter_one_or_raise.return_value = user
        mock_room_service.room_repository.filter_one_or_raise.return_value = room
        mock_room_service.room_user_repository.filter.return_value = room_users
        mock_room_service.room_user_repository.filter_one.return_value = None

        with pytest.raises(MCRDomainError) as exc_info:
            await mock_room_service.join_room(user_id, room_id)

        assert exc_info.value.code == DomainErrorCode.ROOM_IS_FULL
        assert str(room_id) in exc_info.value.message
        assert exc_info.value.details["max_users"] == 4


class TestRoomServiceGameManagement:
    @pytest.mark.asyncio
    async def test_get_available_rooms(self, mock_room_service, user_id, room_id):
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

        mock_room_repo = mock_room_service.room_repository
        mock_room_repo.get_available_rooms_with_users.return_value = [
            (room, [room_user1, room_user2])
        ]

        mock_room_service.user_repository.filter_one_or_raise.side_effect = (
            lambda id=None, **kwargs: {
                user_id: user1,
                user2.id: user2,
            }.get(id or kwargs.get("id"))
        )

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

        guest_user = next(
            (u for u in result[0].users if u.nickname == "GuestUser"), None
        )
        assert guest_user is not None
        assert guest_user.is_ready is False

    @pytest.mark.asyncio
    async def test_end_game_success(self, mock_room_service, user_id, room_id):
        host_id = user_id
        another_user_id = uuid.uuid4()

        room = Room(
            id=room_id,
            name="테스트 방",
            max_users=4,
            is_playing=True,
            host_id=host_id,
        )

        room_users = [
            RoomUser(id=uuid.uuid4(), room_id=room_id, user_id=host_id, is_ready=True),
            RoomUser(
                id=uuid.uuid4(), room_id=room_id, user_id=another_user_id, is_ready=True
            ),
        ]

        mock_room_service.room_repository.filter_one_or_raise.return_value = room
        mock_room_service.room_user_repository.filter.return_value = room_users

        updated_room = Room(
            id=room_id,
            name="테스트 방",
            max_users=4,
            is_playing=False,
            host_id=host_id,
        )

        mock_room_service.room_repository.update.return_value = updated_room

        result = await mock_room_service.end_game(room_id)

        assert result.id == room_id
        assert result.is_playing is False
        mock_room_service.session.commit.assert_awaited_once()
        mock_room_service.room_user_repository.update.assert_called()

    @pytest.mark.asyncio
    async def test_end_game_room_not_found(self, mock_room_service, room_id):
        mock_room_service.room_repository.filter_one_or_raise.side_effect = (
            MCRDomainError(
                code=DomainErrorCode.ROOM_NOT_FOUND,
                message=f"Room with ID {room_id} not found",
                details={"room_id": str(room_id)},
            )
        )

        with pytest.raises(MCRDomainError) as exc_info:
            await mock_room_service.end_game(room_id)

        assert exc_info.value.code == DomainErrorCode.ROOM_NOT_FOUND
        assert str(room_id) in exc_info.value.message

    @pytest.mark.asyncio
    async def test_end_game_room_not_playing(self, mock_room_service, user_id, room_id):
        room = Room(
            id=room_id,
            name="Test Room",
            max_users=4,
            is_playing=False,
            host_id=user_id,
        )

        mock_room_service.room_repository.filter_one_or_raise.return_value = room

        with pytest.raises(MCRDomainError) as exc_info:
            await mock_room_service.end_game(room_id)

        assert exc_info.value.code == DomainErrorCode.ROOM_NOT_PLAYING
        assert str(room_id) in exc_info.value.message

    @pytest.mark.asyncio
    async def test_start_game_success(
        self, mock_room_service, user_id, room_id, mocker
    ):
        room = Room(
            id=room_id,
            name="테스트 방",
            max_users=4,
            is_playing=False,
            host_id=user_id,
            room_number=12345,
        )

        room_users = [
            RoomUser(
                id=uuid.uuid4(), room_id=room_id, user_id=uuid.uuid4(), is_ready=True
            ),
            RoomUser(
                id=uuid.uuid4(), room_id=room_id, user_id=uuid.uuid4(), is_ready=True
            ),
            RoomUser(
                id=uuid.uuid4(), room_id=room_id, user_id=uuid.uuid4(), is_ready=True
            ),
            RoomUser(id=uuid.uuid4(), room_id=room_id, user_id=user_id, is_ready=True),
        ]

        mock_room_service.room_repository.filter_one_or_raise.return_value = room
        mock_room_service.room_user_repository.filter.return_value = room_users

        updated_room = Room(
            id=room_id,
            name="테스트 방",
            max_users=4,
            is_playing=True,
            host_id=user_id,
            room_number=12345,
        )
        mock_room_service.room_repository.update.return_value = updated_room

        game_websocket_url = "ws://game-server/games/12345"

        mocker.patch.object(
            RoomService, "_call_game_server_api", return_value=game_websocket_url
        )

        mock_broadcast = mocker.patch(
            "app.core.room_connection_manager.room_manager.broadcast_game_started"
        )

        result = await mock_room_service.start_game(room_id)

        assert result.id == room_id
        assert result.is_playing is True
        mock_room_service.session.commit.assert_awaited_once()

        RoomService._call_game_server_api.assert_awaited_once()

        mock_broadcast.assert_awaited_once_with(room_id, game_websocket_url)

    @pytest.mark.asyncio
    async def test_start_game_room_not_found(self, mock_room_service, room_id):
        mock_room_service.room_repository.filter_one_or_raise.side_effect = (
            MCRDomainError(
                code=DomainErrorCode.ROOM_NOT_FOUND,
                message=f"Room with ID {room_id} not found",
                details={"room_id": str(room_id)},
            )
        )

        with pytest.raises(MCRDomainError) as exc_info:
            await mock_room_service.start_game(room_id)

        assert exc_info.value.code == DomainErrorCode.ROOM_NOT_FOUND
        assert str(room_id) in exc_info.value.message

    @pytest.mark.asyncio
    async def test_start_game_already_playing(
        self, mock_room_service, user_id, room_id
    ):
        room = Room(
            id=room_id,
            name="테스트 방",
            max_users=4,
            is_playing=True,
            host_id=user_id,
        )

        mock_room_service.room_repository.filter_one_or_raise.return_value = room

        with pytest.raises(MCRDomainError) as exc_info:
            await mock_room_service.start_game(room_id)

        assert exc_info.value.code == DomainErrorCode.ROOM_ALREADY_PLAYING
        assert str(room_id) in exc_info.value.message

    @pytest.mark.asyncio
    async def test_start_game_not_enough_players(
        self, mock_room_service, user_id, room_id
    ):
        room = Room(
            id=room_id,
            name="테스트 방",
            max_users=4,
            is_playing=False,
            host_id=user_id,
        )

        room_users = [
            RoomUser(
                id=uuid.uuid4(), room_id=room_id, user_id=uuid.uuid4(), is_ready=True
            ),
            RoomUser(
                id=uuid.uuid4(), room_id=room_id, user_id=uuid.uuid4(), is_ready=True
            ),
            RoomUser(id=uuid.uuid4(), room_id=room_id, user_id=user_id, is_ready=True),
        ]

        mock_room_service.room_repository.filter_one_or_raise.return_value = room
        mock_room_service.room_user_repository.filter.return_value = room_users

        with pytest.raises(MCRDomainError) as exc_info:
            await mock_room_service.start_game(room_id)

        assert exc_info.value.code == DomainErrorCode.NOT_ENOUGH_PLAYERS
        assert str(room_id) in exc_info.value.message
        assert exc_info.value.details["current_players"] == 3

    @pytest.mark.asyncio
    async def test_start_game_players_not_ready(
        self, mock_room_service, user_id, room_id
    ):
        room = Room(
            id=room_id,
            name="테스트 방",
            max_users=4,
            is_playing=False,
            host_id=user_id,
        )

        room_users = [
            RoomUser(
                id=uuid.uuid4(), room_id=room_id, user_id=uuid.uuid4(), is_ready=True
            ),
            RoomUser(
                id=uuid.uuid4(), room_id=room_id, user_id=uuid.uuid4(), is_ready=True
            ),
            RoomUser(
                id=uuid.uuid4(), room_id=room_id, user_id=uuid.uuid4(), is_ready=True
            ),
            RoomUser(id=uuid.uuid4(), room_id=room_id, user_id=user_id, is_ready=False),
        ]

        mock_room_service.room_repository.filter_one_or_raise.return_value = room
        mock_room_service.room_user_repository.filter.return_value = room_users

        with pytest.raises(MCRDomainError) as exc_info:
            await mock_room_service.start_game(room_id)

        assert exc_info.value.code == DomainErrorCode.PLAYERS_NOT_READY
        assert str(room_id) in exc_info.value.message
        assert exc_info.value.details["not_ready_count"] == 1
