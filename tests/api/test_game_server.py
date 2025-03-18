import uuid

import pytest
from fastapi import status

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.room import Room


@pytest.mark.asyncio
async def test_end_game_success(internal_api_client, mocker):
    room_number = 12345
    room_id = uuid.uuid4()

    room = Room(
        id=room_id,
        name="Test Room",
        room_number=room_number,
        max_users=4,
        is_playing=True,
        host_id=uuid.uuid4(),
    )

    mocker.patch(
        "app.dependencies.repositories.get_room_by_number",
        return_value=room,
    )

    mocker.patch(
        "app.services.room_service.RoomService.end_game",
        return_value=room,
    )

    response = await internal_api_client.post(
        f"/internal/game-server/rooms/{room_number}/end-game"
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Game ended successfully"


@pytest.mark.skip
@pytest.mark.asyncio
async def test_end_game_room_not_found(internal_api_client, mocker):
    room_number = 99999

    mocker.patch(
        "app.dependencies.repositories.get_room_by_number",
        side_effect=MCRDomainError(
            code=DomainErrorCode.ROOM_NOT_FOUND,
            message=f"Room with number {room_number} not found",
            details={"room_number": room_number},
        ),
    )

    response = await internal_api_client.post(
        f"/internal/game-server/rooms/{room_number}/end-game"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["code"] == DomainErrorCode.ROOM_NOT_FOUND.value
    assert "room_number" in data["error_details"]
    assert data["error_details"]["room_number"] == room_number


@pytest.mark.skip
@pytest.mark.asyncio
async def test_end_game_room_not_playing(internal_api_client, mocker):
    room_number = 12345
    room_id = uuid.uuid4()

    room = Room(
        id=room_id,
        name="Test Room",
        room_number=room_number,
        max_users=4,
        is_playing=False,
        host_id=uuid.uuid4(),
    )

    mocker.patch(
        "app.dependencies.repositories.get_room_by_number",
        return_value=room,
    )

    mocker.patch(
        "app.services.room_service.RoomService.end_game",
        side_effect=MCRDomainError(
            code=DomainErrorCode.ROOM_NOT_PLAYING,
            message=f"Room with ID {room_id} is not currently playing",
            details={"room_id": str(room_id)},
        ),
    )

    response = await internal_api_client.post(
        f"/internal/game-server/rooms/{room_number}/end-game"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == DomainErrorCode.ROOM_NOT_PLAYING.value
    assert "room_id" in data["error_details"]
    assert data["error_details"]["room_id"] == str(room_id)
