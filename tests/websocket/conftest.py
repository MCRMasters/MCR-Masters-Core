import asyncio
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import WebSocket
from httpx import ASGITransport, AsyncClient

from app.core.room_connection_manager import room_manager
from app.main import app
from app.models.room import Room
from app.models.room_user import RoomUser
from app.models.user import User
from app.schemas.auth.base import TokenResponse


async def _create_google_oauth_response(message):
    """Google OAuth 메시지에 대한 응답을 생성합니다."""
    if message.get("action") == "get_oauth_url":
        return {"action": "oauth_url", "auth_url": "https://mock.auth.url"}
    elif message.get("action") == "auth":
        if "code" not in message or not message["code"]:
            return {"error": "No code in auth"}
        elif message["code"] == "test_code":
            token_response = TokenResponse(
                access_token="mock_access_token",
                refresh_token="mock_refresh_token",
                is_new_user=True,
            )
            return {
                "action": "auth_success",
                "access_token": token_response.access_token,
                "refresh_token": token_response.refresh_token,
                "is_new_user": token_response.is_new_user,
                "token_type": token_response.token_type,
            }
        else:
            return {"error": "Invalid OAuth code"}
    else:
        return {"error": f"Invalid action: {message['action']}"}


def _setup_websocket_queues(mock_websocket):
    """WebSocket 메시지 큐를 설정합니다."""
    send_queue = asyncio.Queue()
    receive_queue = asyncio.Queue()

    async def mock_send_json(message):
        await send_queue.put(message)

    async def mock_receive_json():
        if not receive_queue.empty():
            return await receive_queue.get()
        return {}

    mock_websocket.send_json.side_effect = mock_send_json
    mock_websocket.receive_json.side_effect = mock_receive_json

    return send_queue, receive_queue


@pytest_asyncio.fixture
async def mock_websocket_client(mocker):
    """
    WebSocket 테스트를 위한 모의 클라이언트를 생성합니다.
    비동기 WebSocket 상호작용을 시뮬레이션합니다.
    """
    mock_websocket = mocker.AsyncMock(spec=WebSocket)

    # WebSocket 메시지 큐 설정
    send_queue, receive_queue = _setup_websocket_queues(mock_websocket)

    # 메시지 시뮬레이션 메서드 추가
    async def simulate_message(message):
        await receive_queue.put(message)

    mock_websocket.simulate_message = simulate_message

    # Google OAuth 메시지 핸들러 추가
    mock_websocket.handle_google_oauth_message = _create_google_oauth_response

    # 자동 응답 설정
    original_send_json = mock_websocket.send_json

    async def auto_respond_send_json(message):
        await original_send_json(message)
        response = await _create_google_oauth_response(message)
        await receive_queue.put(response)

    mock_websocket.auto_respond = False
    mock_websocket.send_json_and_get_response = auto_respond_send_json

    return mock_websocket


@pytest_asyncio.fixture
async def client():
    """
    테스트용 FastAPI 클라이언트를 생성합니다.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def test_user_data():
    """테스트용 사용자 데이터를 생성합니다."""
    return {
        "id": uuid4(),
        "uid": "123456789",
        "nickname": "TestUser",
        "email": "test@example.com",
    }


@pytest_asyncio.fixture
async def test_room_data(test_user_data):
    """테스트용 방 데이터를 생성합니다."""
    return {
        "id": uuid4(),
        "name": "테스트 방",
        "room_number": 12345,
        "max_users": 4,
        "is_playing": False,
        "host_id": test_user_data["id"],
    }


def _setup_room_ws_queues(mock_websocket):
    """방 WebSocket 메시지 큐를 설정합니다."""
    send_queue = asyncio.Queue()
    receive_queue = asyncio.Queue()

    async def mock_send_json(message):
        await send_queue.put(message)

    async def mock_receive_json():
        if not receive_queue.empty():
            return await receive_queue.get()
        return {}

    mock_websocket.send_json.side_effect = mock_send_json
    mock_websocket.receive_json.side_effect = mock_receive_json

    return send_queue, receive_queue


@pytest_asyncio.fixture
async def room_ws_client(mocker, test_user_data, test_room_data):
    """
    방 WebSocket 연결 테스트를 위한 모의 클라이언트를 생성합니다.
    """
    mock_websocket = mocker.AsyncMock(spec=WebSocket)

    # 헤더 모의
    mock_headers = mocker.MagicMock()
    mock_headers.get.return_value = "Bearer test_token"
    mock_websocket.headers = mock_headers

    # close 메서드 설정
    mock_websocket.close.return_value = None

    # 사용자 모델 생성
    user = User(
        id=test_user_data["id"],
        uid=test_user_data["uid"],
        nickname=test_user_data["nickname"],
        email=test_user_data["email"],
    )

    # 방 모델 생성
    room = Room(
        id=test_room_data["id"],
        name=test_room_data["name"],
        room_number=test_room_data["room_number"],
        max_users=test_room_data["max_users"],
        is_playing=test_room_data["is_playing"],
        host_id=test_room_data["host_id"],
    )

    # 방 사용자 모델 생성
    room_user = RoomUser(
        id=uuid4(),
        room_id=room.id,
        user_id=user.id,
        is_ready=False,
    )

    # 비동기 JSON 송수신 설정
    send_queue, receive_queue = _setup_room_ws_queues(mock_websocket)

    # client_state 모킹
    client_state = mocker.MagicMock()
    client_state.CONNECTED = True
    mock_websocket.client_state = client_state

    # 메시지 시뮬레이션 메서드
    async def simulate_message(message):
        await receive_queue.put(message)

    mock_websocket.simulate_message = simulate_message

    # 테스트에 필요한 데이터를 저장
    mock_websocket.test_data = {
        "user": user,
        "room": room,
        "room_user": room_user,
    }

    yield mock_websocket


@pytest.fixture
def mock_room_connection_manager(mocker):
    """RoomConnectionManager를 모킹합니다."""
    original_manager = room_manager

    # 테스트 종료 후 원래 매니저로 복원
    yield mocker.MagicMock(spec=original_manager)
