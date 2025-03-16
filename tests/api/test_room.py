import uuid

import pytest
from fastapi import status

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.room import Room


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
