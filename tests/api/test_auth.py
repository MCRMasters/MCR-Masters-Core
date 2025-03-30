from unittest.mock import ANY, Mock

import pytest
from fastapi import status

from app.schemas.auth.base import TokenResponse


@pytest.mark.asyncio
async def test_get_google_login_url(client):
    client_instance, mocks = client

    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        "client_id=secret&response_type=code&redirect_uri=http://localhost:8000/api/v1/auth/login/google/callback&"
        "scope=openid+email+profile&access_type=offline&prompt=consent&state=test_state"
    )
    mocks["services"]["google_service"].get_authorization_url = Mock(
        return_value=auth_url
    )

    response = await client_instance.get("/api/v1/auth/login/google")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "auth_url" in data
    assert "session_id" in data
    assert "accounts.google.com" in data["auth_url"]
    mocks["services"]["google_service"].get_authorization_url.assert_called_once_with(
        state=ANY
    )


@pytest.mark.asyncio
async def test_google_callback_success(client):
    client_instance, mocks = client

    token_response = TokenResponse(
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        is_new_user=True,
        token_type="bearer",
    )
    mocks["services"][
        "google_service"
    ].process_google_login.return_value = token_response

    response = await client_instance.get(
        "/api/v1/auth/login/google/callback?code=test_code&state=test_state"
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert data["message"] == "Login completed. Please go back to game."

    mocks["services"]["google_service"].process_google_login.assert_called_once_with(
        "test_code"
    )


@pytest.mark.asyncio
async def test_google_callback_error(client):
    client_instance, mocks = client

    from fastapi import HTTPException

    error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to get token from Google",
    )
    mocks["services"]["google_service"].process_google_login.side_effect = error

    response = await client_instance.get(
        "/api/v1/auth/login/google/callback?code=invalid_code&state=invalid_state"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Failed to get token from Google"

    mocks["services"]["google_service"].process_google_login.assert_called_once_with(
        "invalid_code"
    )
