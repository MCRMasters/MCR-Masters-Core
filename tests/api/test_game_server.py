import uuid

import pytest
from fastapi import status

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.room import Room


@pytest.mark.asyncio
async def test_end_game_success(login_client):
    client, mocks = login_client

    # 방 정보 설정
    room_number = 12345
    room_id = uuid.uuid4()
    host_id = uuid.uuid4()

    # 게임 종료 후 업데이트된 방 객체 모킹
    updated_room = Room(
        id=room_id,
        name="Test Room",
        room_number=room_number,
        max_users=4,
        is_playing=False,
        host_id=host_id,
    )

    # 라우터에서 사용할 의존성 응답 모킹
    mocks["services"]["room_service"].end_game.return_value = updated_room

    # API 호출
    response = await client.post(f"/internal/game-server/rooms/{room_number}/end-game")

    # 응답 검증
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Game ended successfully"

    # 서비스 호출 검증 - get_room_by_number로부터 room을 받아옴
    # 직접적인 호출 검증이 어렵지만 호출 자체는 검증
    mocks["services"]["room_service"].end_game.assert_called_once()


@pytest.mark.asyncio
async def test_end_game_room_not_found(login_client):
    client, mocks = login_client

    # 방 번호 설정
    room_number = 99999

    # room_service.end_game에서 예외 발생 모킹
    error = MCRDomainError(
        code=DomainErrorCode.ROOM_NOT_FOUND,
        message=f"Room with number {room_number} not found",
        details={"room_number": room_number},
    )

    mocks["services"]["room_service"].end_game.side_effect = error

    # API 호출
    response = await client.post(f"/internal/game-server/rooms/{room_number}/end-game")

    # 응답 검증
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["code"] == DomainErrorCode.ROOM_NOT_FOUND.value
    assert "room_number" in data["error_details"]
    assert data["error_details"]["room_number"] == room_number


@pytest.mark.asyncio
async def test_end_game_room_not_playing(login_client):
    client, mocks = login_client

    # 방 정보 설정
    room_number = 12345
    room_id = uuid.uuid4()

    # 게임 중이 아닌 방에 대한 에러 모킹
    error = MCRDomainError(
        code=DomainErrorCode.ROOM_NOT_PLAYING,
        message=f"Room with ID {room_id} is not currently playing",
        details={"room_id": str(room_id)},
    )

    mocks["services"]["room_service"].end_game.side_effect = error

    # API 호출
    response = await client.post(f"/internal/game-server/rooms/{room_number}/end-game")

    # 응답 검증
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == DomainErrorCode.ROOM_NOT_PLAYING.value
    assert "room_id" in data["error_details"]
    assert data["error_details"]["room_id"] == str(room_id)
