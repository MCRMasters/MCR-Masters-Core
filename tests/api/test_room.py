import uuid

import pytest
from fastapi import status

from app.core.error import DomainErrorCode, MCRDomainError
from app.dependencies.repositories import get_room_by_number
from app.main import app
from app.models.room import Room
from app.models.room_user import RoomUser
from app.schemas.room import AvailableRoomResponse, RoomUserResponse


@pytest.mark.asyncio
async def test_create_room_success(login_client, mock_user):
    client, mocks = login_client
    room_id = uuid.uuid4()
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        room_number=12345,
        max_users=4,
        is_playing=False,
        host_id=mock_user.id,
    )
    mocks["services"]["room_service"].create_room.return_value = room
    response = await client.post("/api/v1/room")
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "엄숙한 패황전"
    assert data["room_number"] == 12345
    mocks["services"]["room_service"].create_room.assert_called_once_with(
        current_user_id=mock_user.id
    )


@pytest.mark.asyncio
async def test_create_room_unauthorized(client):
    client_instance, _ = client
    response = await client_instance.post("/api/v1/room")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_create_room_user_not_found(login_client, mock_user):
    client, mocks = login_client
    error = MCRDomainError(
        code=DomainErrorCode.USER_NOT_FOUND,
        message=f"User with ID {mock_user.id} not found",
        details={"user_id": str(mock_user.id)},
    )
    mocks["services"]["room_service"].create_room.side_effect = error
    response = await client.post("/api/v1/room")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["code"] == DomainErrorCode.USER_NOT_FOUND.value
    assert "user_id" in data["error_details"]
    assert data["error_details"]["user_id"] == str(mock_user.id)


@pytest.mark.asyncio
async def test_join_room_success(login_client, mock_user):
    client, mocks = login_client
    room_number = 12345
    test_room = Room(
        id=uuid.uuid4(),
        name="Test Room",
        room_number=room_number,
        max_users=4,
        is_playing=False,
        host_id=mock_user.id,
    )
    app.dependency_overrides[get_room_by_number] = lambda: test_room
    room_user = RoomUser(
        id=uuid.uuid4(),
        room_id=test_room.id,
        user_id=mock_user.id,
        user_uid=mock_user.uid,
        user_nickname=mock_user.nickname,
        is_ready=False,
        slot_index=0,
    )
    mocks["services"]["room_service"].join_room.return_value = room_user
    response = await client.post(f"/api/v1/room/{room_number}/join")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == test_room.name
    assert data["room_number"] == room_number
    assert data["slot_index"] == room_user.slot_index
    mocks["services"]["room_service"].join_room.assert_called_once()
    app.dependency_overrides.pop(get_room_by_number, None)


@pytest.mark.asyncio
async def test_join_room_unauthorized(client):
    client_instance, _ = client
    room_number = 12345
    response = await client_instance.post(f"/api/v1/room/{room_number}/join")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_join_room_not_found(login_client, mock_user):
    client, mocks = login_client
    room_number = 99999
    error = MCRDomainError(
        code=DomainErrorCode.ROOM_NOT_FOUND,
        message=f"Room with number {room_number} not found",
        details={"room_number": room_number},
    )

    async def mock_get_room_by_number():
        raise error

    app.dependency_overrides[get_room_by_number] = mock_get_room_by_number
    try:
        response = await client.post(f"/api/v1/room/{room_number}/join")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["code"] == DomainErrorCode.ROOM_NOT_FOUND.value
        assert "room_number" in data["error_details"]
        assert data["error_details"]["room_number"] == room_number
    finally:
        app.dependency_overrides.pop(get_room_by_number, None)


@pytest.mark.asyncio
async def test_join_room_is_full(login_client, mock_user):
    client, mocks = login_client
    room_number = 12345
    error = MCRDomainError(
        code=DomainErrorCode.ROOM_IS_FULL,
        message=f"Room with number {room_number} is full",
        details={"room_number": room_number, "max_users": 4},
    )
    mocks["services"]["room_service"].join_room.side_effect = error
    response = await client.post(f"/api/v1/room/{room_number}/join")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == DomainErrorCode.ROOM_IS_FULL.value
    assert "room_number" in data["error_details"]
    assert data["error_details"]["room_number"] == room_number


@pytest.mark.asyncio
async def test_join_room_user_already_in_room(login_client, mock_user):
    client, mocks = login_client
    room_number = 12345
    another_room_id = uuid.uuid4()
    error = MCRDomainError(
        code=DomainErrorCode.USER_ALREADY_IN_ROOM,
        message=f"User with ID {mock_user.id} is already in a room",
        details={
            "user_id": str(mock_user.id),
            "current_room_id": str(another_room_id),
        },
    )
    mocks["services"]["room_service"].join_room.side_effect = error
    response = await client.post(f"/api/v1/room/{room_number}/join")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == DomainErrorCode.USER_ALREADY_IN_ROOM.value
    assert "user_id" in data["error_details"]
    assert data["error_details"]["user_id"] == str(mock_user.id)


@pytest.mark.asyncio
async def test_get_available_rooms_success(login_client, mock_user):
    client, mocks = login_client
    mock_response = [
        AvailableRoomResponse(
            name="Test Room 1",
            room_number=123,
            max_users=4,
            current_users=2,
            host_nickname="HostUser",
            host_uid="HostUserUid",
            users=[
                RoomUserResponse(
                    user_uid="HostUserUid",
                    nickname="HostUser",
                    is_ready=True,
                    slot_index=0,
                ),
                RoomUserResponse(
                    user_uid="GuestUserUid",
                    nickname="GuestUser",
                    is_ready=False,
                    slot_index=1,
                ),
            ],
        ),
        AvailableRoomResponse(
            name="Test Room 2",
            room_number=456,
            max_users=4,
            current_users=1,
            host_nickname="AnotherHost",
            host_uid="AnotherHostUid",
            users=[
                RoomUserResponse(
                    user_uid="AnotherHostUid",
                    nickname="AnotherHost",
                    is_ready=False,
                    slot_index=0,
                )
            ],
        ),
    ]
    mocks["services"]["room_service"].get_available_rooms.return_value = mock_response
    response = await client.get("/api/v1/room")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Test Room 1"
    assert data[0]["room_number"] == 123
    assert data[0]["max_users"] == 4
    assert data[0]["current_users"] == 2
    assert data[0]["host_nickname"] == "HostUser"
    assert len(data[0]["users"]) == 2
    assert data[1]["name"] == "Test Room 2"
    assert data[1]["room_number"] == 456
    assert data[1]["max_users"] == 4
    assert data[1]["current_users"] == 1
    assert data[1]["host_nickname"] == "AnotherHost"
    assert len(data[1]["users"]) == 1
    mocks["services"]["room_service"].get_available_rooms.assert_called_once()


@pytest.mark.asyncio
async def test_get_available_rooms_unauthorized(client):
    client_instance, _ = client
    response = await client_instance.get("/api/v1/room")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
