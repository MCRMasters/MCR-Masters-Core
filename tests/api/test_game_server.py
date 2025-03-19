import uuid

import pytest
from fastapi import status

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.room import Room


@pytest.mark.asyncio
async def test_end_game_success(login_client):
    client, mocks = login_client

    room_number = 12345
    room_id = uuid.uuid4()
    host_id = uuid.uuid4()

    updated_room = Room(
        id=room_id,
        name="Test Room",
        room_number=room_number,
        max_users=4,
        is_playing=False,
        host_id=host_id,
    )

    mocks["services"]["room_service"].end_game.return_value = updated_room

    response = await client.post(f"/internal/game-server/rooms/{room_number}/end-game")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Game ended successfully"

    mocks["services"]["room_service"].end_game.assert_called_once()


@pytest.mark.asyncio
async def test_end_game_room_not_found(login_client):
    client, mocks = login_client

    room_number = 99999

    error = MCRDomainError(
        code=DomainErrorCode.ROOM_NOT_FOUND,
        message=f"Room with number {room_number} not found",
        details={"room_number": room_number},
    )

    mocks["services"]["room_service"].end_game.side_effect = error

    response = await client.post(f"/internal/game-server/rooms/{room_number}/end-game")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["code"] == DomainErrorCode.ROOM_NOT_FOUND.value
    assert "room_number" in data["error_details"]
    assert data["error_details"]["room_number"] == room_number


@pytest.mark.asyncio
async def test_end_game_room_not_playing(login_client):
    client, mocks = login_client

    room_number = 12345
    room_id = uuid.uuid4()

    error = MCRDomainError(
        code=DomainErrorCode.ROOM_NOT_PLAYING,
        message=f"Room with ID {room_id} is not currently playing",
        details={"room_id": str(room_id)},
    )

    mocks["services"]["room_service"].end_game.side_effect = error

    response = await client.post(f"/internal/game-server/rooms/{room_number}/end-game")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == DomainErrorCode.ROOM_NOT_PLAYING.value
    assert "room_id" in data["error_details"]
    assert data["error_details"]["room_id"] == str(room_id)
