import asyncio
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.session import get_session
from app.dependencies.auth import get_current_user
from app.dependencies.repositories import (
    get_room_repository,
    get_room_user_repository,
    get_user_repository,
)
from app.dependencies.services import (
    get_google_oauth_service,
    get_room_service,
    get_user_service,
)
from app.main import app
from app.models.user import User
from app.schemas.auth.base import TokenResponse
from app.schemas.auth.google import GoogleTokenResponse, GoogleUserInfo


@pytest.fixture
def mock_user():
    """
    기본 모의 사용자 객체를 생성합니다.
    API 테스트에서 인증된 사용자를 시뮬레이션합니다.
    """
    return User(
        email="test@example.com",
        uid="123456789",
        nickname="",
        last_login=None,
    )


@pytest.fixture
def mock_google_responses():
    """
    Google OAuth 응답을 모의로 생성합니다.
    OAuth 흐름을 테스트하는 데 사용됩니다.
    """
    return {
        "token_response": GoogleTokenResponse(
            access_token="mock_access_token",
            refresh_token="mock_refresh_token",
            id_token="mock_id_token",
            expires_in=3600,
            token_type="Bearer",
            scope="openid email profile",
        ).model_dump(),
        "userinfo_response": GoogleUserInfo(
            email="test@example.com",
            name="Test User",
            picture="https://example.com/picture.jpg",
            verified_email=True,
            locale="en",
        ).model_dump(),
    }


@pytest_asyncio.fixture
async def client(
    mock_session,
    mock_user_repository,
    mock_room_repository,
    mock_room_user_repository,
    mock_user_service,
    mock_google_service,
    mock_room_service,
):
    """
    테스트용 FastAPI 클라이언트를 생성합니다.
    의존성을 모의(mock)로 대체하여 격리된 API 테스트 환경을 제공합니다.
    """
    # 의존성 오버라이드
    app.dependency_overrides[get_session] = lambda: mock_session

    app.dependency_overrides[get_user_repository] = lambda: mock_user_repository
    app.dependency_overrides[get_room_repository] = lambda: mock_room_repository
    app.dependency_overrides[get_room_user_repository] = (
        lambda: mock_room_user_repository
    )

    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    app.dependency_overrides[get_google_oauth_service] = lambda: mock_google_service
    app.dependency_overrides[get_room_service] = lambda: mock_room_service

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    # 테스트 후 의존성 오버라이드 초기화
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def login_client(
    mock_session,
    mock_auth,
    mock_user_repository,
    mock_room_repository,
    mock_room_user_repository,
    mock_user_service,
    mock_google_service,
    mock_room_service,
):
    """
    인증된 상태의 테스트 클라이언트를 생성합니다.
    현재 사용자 인증 의존성을 모의(mock)로 대체합니다.
    """
    app.dependency_overrides[get_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_auth

    app.dependency_overrides[get_user_repository] = lambda: mock_user_repository
    app.dependency_overrides[get_room_repository] = lambda: mock_room_repository
    app.dependency_overrides[get_room_user_repository] = (
        lambda: mock_room_user_repository
    )

    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    app.dependency_overrides[get_google_oauth_service] = lambda: mock_google_service
    app.dependency_overrides[get_room_service] = lambda: mock_room_service

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": "Bearer test_token"},
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_auth(mocker, mock_user):
    """
    모의 사용자 인증 픽스처
    토큰에서 사용자 ID를 추출하는 로직을 모의합니다.
    """
    mocker.patch(
        "app.dependencies.auth.get_user_id_from_token",
        return_value=mock_user.id,
    )

    return mock_user


@pytest_asyncio.fixture
async def mock_websocket_client(mocker):
    """
    WebSocket 테스트를 위한 모의 클라이언트를 생성합니다.
    비동기 WebSocket 상호작용을 시뮬레이션합니다.
    """
    mock_websocket = AsyncMock()

    send_queue = asyncio.Queue()
    receive_queue = asyncio.Queue()

    async def mock_send_json(message):
        await send_queue.put(message)

        if message["action"] == "get_oauth_url":
            await receive_queue.put(
                {"action": "oauth_url", "auth_url": "https://mock.auth.url"},
            )
        elif message["action"] == "auth":
            if "code" not in message or not message["code"]:
                await receive_queue.put({"error": "No code in auth"})
            elif message["code"] == "test_code":
                token_response = TokenResponse(
                    access_token="mock_access_token",
                    refresh_token="mock_refresh_token",
                    is_new_user=True,
                )
                await receive_queue.put(
                    {
                        "action": "auth_success",
                        "access_token": token_response.access_token,
                        "refresh_token": token_response.refresh_token,
                        "is_new_user": token_response.is_new_user,
                        "token_type": token_response.token_type,
                    },
                )
            else:
                await receive_queue.put({"error": "Invalid OAuth code"})
        else:
            await receive_queue.put({"error": f"Invalid action: {message['action']}"})

    async def mock_receive_json():
        return await receive_queue.get()

    mock_websocket.send_json.side_effect = mock_send_json
    mock_websocket.receive_json.side_effect = mock_receive_json

    return mock_websocket
