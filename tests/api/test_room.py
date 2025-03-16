import uuid

import pytest
from fastapi import status

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.room import Room
from app.models.room_user import RoomUser


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
