from unittest.mock import Mock

import pytest
from fastapi import status

from app.schemas.auth.base import TokenResponse


@pytest.mark.asyncio
async def test_get_google_login_url(client):
    client_instance, mocks = client

    # Google 인증 URL 모킹
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?client_id=secret&response_type=code&redirect_uri=http://localhost:8000/api/v1/auth/login/google/callback&scope=openid+email+profile&access_type=offline&prompt=consent"

    mocks["services"]["google_service"].get_authorization_url = Mock(
        return_value=auth_url
    )

    # API 호출
    response = await client_instance.get("/api/v1/auth/login/google")

    # 응답 검증
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "auth_url" in data
    assert "accounts.google.com" in data["auth_url"]

    # 서비스 호출 검증
    mocks["services"]["google_service"].get_authorization_url.assert_called_once()


@pytest.mark.asyncio
async def test_google_callback_success(client):
    client_instance, mocks = client

    # Google 로그인 프로세스 결과 모킹
    token_response = TokenResponse(
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        is_new_user=True,
        token_type="bearer",
    )
    mocks["services"][
        "google_service"
    ].process_google_login.return_value = token_response

    # API 호출
    response = await client_instance.get(
        "/api/v1/auth/login/google/callback?code=test_code"
    )

    # 응답 검증
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["is_new_user"] is True
    assert data["token_type"] == "bearer"

    # 서비스 호출 검증 - code 파라미터가 정확히 전달되는지 확인
    mocks["services"]["google_service"].process_google_login.assert_called_once_with(
        "test_code"
    )


@pytest.mark.asyncio
async def test_google_callback_error(client):
    client_instance, mocks = client

    # 에러 모킹
    from fastapi import HTTPException

    error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to get token from Google",
    )
    mocks["services"]["google_service"].process_google_login.side_effect = error

    # API 호출
    response = await client_instance.get(
        "/api/v1/auth/login/google/callback?code=invalid_code"
    )

    # 응답 검증
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Failed to get token from Google"

    # 서비스 호출 검증 - code 파라미터가 정확히 전달되는지 확인
    mocks["services"]["google_service"].process_google_login.assert_called_once_with(
        "invalid_code"
    )
