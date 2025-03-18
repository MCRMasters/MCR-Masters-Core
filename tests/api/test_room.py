import uuid

import pytest
from fastapi import status

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.room import Room
from app.models.room_user import RoomUser
from app.schemas.room import AvailableRoomResponse, RoomUserResponse


@pytest.mark.asyncio
async def test_create_room_success(login_client, mock_user, mocker):
    room_id = uuid.uuid4()
    room = Room(
        id=room_id,
        name="엄숙한 패황전",
        room_number=12345,
        max_users=4,
        is_playing=False,
        host_id=mock_user.id,
    )

    mocker.patch(
        "app.services.room_service.RoomService.create_room",
        return_value=room,
    )

    response = await login_client.post("/api/v1/room")

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "엄숙한 패황전"
    assert data["room_number"] == 12345


@pytest.mark.asyncio
async def test_create_room_unauthorized(client):
    response = await client.post("/api/v1/room")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_create_room_user_not_found(login_client, mock_user, mocker):
    mocker.patch(
        "app.services.room_service.RoomService.create_room",
        side_effect=MCRDomainError(
            code=DomainErrorCode.USER_NOT_FOUND,
            message=f"User with ID {mock_user.id} not found",
            details={"user_id": str(mock_user.id)},
        ),
    )

    response = await login_client.post("/api/v1/room")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["code"] == DomainErrorCode.USER_NOT_FOUND.value
    assert "user_id" in data["error_details"]
    assert data["error_details"]["user_id"] == str(mock_user.id)


@pytest.mark.asyncio
async def test_join_room_success(login_client, mock_user, mocker):
    room_number = 12345
    room_user = RoomUser(
        id=uuid.uuid4(),
        room_id=uuid.uuid4(),
        user_id=mock_user.id,
        is_ready=False,
    )

    mocker.patch(
        "app.services.room_service.RoomService.join_room",
        return_value=room_user,
    )

    response = await login_client.post(f"/api/v1/room/{room_number}/join")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Room joined successfully"


@pytest.mark.asyncio
async def test_join_room_unauthorized(client):
    room_number = 12345
    response = await client.post(f"/api/v1/room/{room_number}/join")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_join_room_not_found(login_client, mock_user, mocker):
    room_number = 99999
    mocker.patch(
        "app.services.room_service.RoomService.join_room",
        side_effect=MCRDomainError(
            code=DomainErrorCode.ROOM_NOT_FOUND,
            message=f"Room with number {room_number} not found",
            details={"room_number": room_number},
        ),
    )

    response = await login_client.post(f"/api/v1/room/{room_number}/join")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["code"] == DomainErrorCode.ROOM_NOT_FOUND.value
    assert "room_number" in data["error_details"]
    assert data["error_details"]["room_number"] == room_number


@pytest.mark.asyncio
async def test_join_room_is_full(login_client, mock_user, mocker):
    room_number = 12345
    mocker.patch(
        "app.services.room_service.RoomService.join_room",
        side_effect=MCRDomainError(
            code=DomainErrorCode.ROOM_IS_FULL,
            message=f"Room with number {room_number} is full",
            details={"room_number": room_number, "max_users": 4},
        ),
    )

    response = await login_client.post(f"/api/v1/room/{room_number}/join")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == DomainErrorCode.ROOM_IS_FULL.value
    assert "room_number" in data["error_details"]
    assert data["error_details"]["room_number"] == room_number


@pytest.mark.asyncio
async def test_join_room_already_playing(login_client, mock_user, mocker):
    room_number = 12345
    mocker.patch(
        "app.services.room_service.RoomService.join_room",
        side_effect=MCRDomainError(
            code=DomainErrorCode.ROOM_ALREADY_PLAYING,
            message=f"Room with number {room_number} is already playing",
            details={"room_number": room_number},
        ),
    )

    response = await login_client.post(f"/api/v1/room/{room_number}/join")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == DomainErrorCode.ROOM_ALREADY_PLAYING.value
    assert "room_number" in data["error_details"]
    assert data["error_details"]["room_number"] == room_number


@pytest.mark.asyncio
async def test_join_room_user_already_in_room(login_client, mock_user, mocker):
    room_number = 12345
    another_room_number = 54321
    mocker.patch(
        "app.services.room_service.RoomService.join_room",
        side_effect=MCRDomainError(
            code=DomainErrorCode.USER_ALREADY_IN_ROOM,
            message=f"User with ID {mock_user.id} is already in a room",
            details={
                "user_id": str(mock_user.id),
                "current_room_number": another_room_number,
            },
        ),
    )

    response = await login_client.post(f"/api/v1/room/{room_number}/join")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == DomainErrorCode.USER_ALREADY_IN_ROOM.value
    assert "user_id" in data["error_details"]
    assert data["error_details"]["user_id"] == str(mock_user.id)
    assert "current_room_number" in data["error_details"]
    assert data["error_details"]["current_room_number"] == another_room_number


@pytest.mark.asyncio
async def test_get_available_rooms_success(login_client, mock_user, mocker):
    mock_response = [
        AvailableRoomResponse(
            name="Test Room 1",
            room_number=123,
            max_users=4,
            current_users=2,
            host_nickname="HostUser",
            users=[
                RoomUserResponse(nickname="HostUser", is_ready=True),
                RoomUserResponse(nickname="GuestUser", is_ready=False),
            ],
        ),
        AvailableRoomResponse(
            name="Test Room 2",
            room_number=456,
            max_users=4,
            current_users=1,
            host_nickname="AnotherHost",
            users=[RoomUserResponse(nickname="AnotherHost", is_ready=False)],
        ),
    ]

    mocker.patch(
        "app.services.room_service.RoomService.get_available_rooms",
        return_value=mock_response,
    )

    response = await login_client.get("/api/v1/room")

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


@pytest.mark.asyncio
async def test_get_available_rooms_unauthorized(client):
    response = await client.get("/api/v1/room")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
