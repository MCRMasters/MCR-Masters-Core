import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import status

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.room import Room


# test_game_server.py에서 사용할 mock_session 픽스처 재정의
@pytest.fixture
def mock_session(mocker):
    """게임 서버 테스트를 위한 mock_session 픽스처"""
    session = AsyncMock()

    # 기본적으로 execute 메서드는 AsyncMock으로 설정
    session.execute = AsyncMock()

    return session


@pytest.mark.asyncio
async def test_end_game_success(client, mocker, mock_session):
    room_number = 12345
    room_id = uuid.uuid4()
    host_id = uuid.uuid4()

    room = Room(
        id=room_id,
        name="Test Room",
        room_number=room_number,
        max_users=4,
        is_playing=True,
        host_id=host_id,
    )

    mock_result = mocker.Mock()
    mock_result.scalar_one_or_none.return_value = room
    mock_session.execute.return_value = mock_result

    updated_room = Room(
        id=room_id,
        name="Test Room",
        room_number=room_number,
        max_users=4,
        is_playing=False,
        host_id=host_id,
    )

    mocker.patch(
        "app.services.room_service.RoomService.end_game", return_value=updated_room
    )

    response = await client.post(f"/internal/game-server/rooms/{room_number}/end-game")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Game ended successfully"


@pytest.mark.asyncio
async def test_end_game_room_not_found(client, mocker, mock_session):
    room_number = 99999

    # Room not found 예외 생성
    error = MCRDomainError(
        code=DomainErrorCode.ROOM_NOT_FOUND,
        message=f"Room with number {room_number} not found",
        details={"room_number": room_number},
    )

    mock_result = mocker.Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    mocker.patch("app.dependencies.repositories.get_room_by_number", side_effect=error)

    response = await client.post(f"/internal/game-server/rooms/{room_number}/end-game")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["code"] == DomainErrorCode.ROOM_NOT_FOUND.value
    assert "room_number" in data["error_details"]
    assert data["error_details"]["room_number"] == room_number


@pytest.mark.asyncio
async def test_end_game_room_not_playing(client, mocker, mock_session):
    room_number = 12345
    room_id = uuid.uuid4()
    host_id = uuid.uuid4()

    room = Room(
        id=room_id,
        name="Test Room",
        room_number=room_number,
        max_users=4,
        is_playing=False,
        host_id=host_id,
    )

    mock_result = mocker.Mock()
    mock_result.scalar_one_or_none.return_value = room
    mock_session.execute.return_value = mock_result

    error = MCRDomainError(
        code=DomainErrorCode.ROOM_NOT_PLAYING,
        message=f"Room with ID {room_id} is not currently playing",
        details={"room_id": str(room_id)},
    )

    mocker.patch("app.services.room_service.RoomService.end_game", side_effect=error)

    response = await client.post(f"/internal/game-server/rooms/{room_number}/end-game")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == DomainErrorCode.ROOM_NOT_PLAYING.value
    assert "room_id" in data["error_details"]
    assert data["error_details"]["room_id"] == str(room_id)
