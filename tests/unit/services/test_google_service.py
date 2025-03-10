import pytest
from fastapi import HTTPException, status
from httpx import HTTPStatusError

from app.services.auth.google import GoogleOAuthService


@pytest.mark.asyncio
async def test_get_google_token_success(mock_google_client, mock_google_responses):
    """Google 토큰 획득 성공 테스트"""
    token_response = await GoogleOAuthService.get_google_token("test_code")

    assert token_response.access_token == "mock_access_token"
    assert token_response.refresh_token == "mock_refresh_token"
    mock_google_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_get_google_token_failure(mocker):
    mocker.patch(
        "httpx.AsyncClient.post",
        side_effect=HTTPStatusError(
            "Token request failed",
            request=mocker.Mock(),
            response=mocker.Mock(status_code=400),
        ),
    )
    with pytest.raises(HTTPStatusError):
        await GoogleOAuthService.get_google_token("invalid_code")


@pytest.mark.asyncio
async def test_get_user_info_success(mock_google_client, mock_google_responses):
    user_info = await GoogleOAuthService.get_user_info("mock_access_token")

    assert user_info.email == "test@example.com"
    assert user_info.name == "Test User"
    mock_google_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_google_login_success(
    mock_google_client,
    mock_session,
    mock_user,
):
    login_response = await GoogleOAuthService.process_google_login(
        "test_code",
        mock_session,
    )

    assert login_response.is_new_user is True
    assert "access_token" in login_response.model_dump()
    assert "refresh_token" in login_response.model_dump()

    mock_google_client.post.assert_called_once()
    mock_google_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_google_login_failure(mock_session, mocker):
    mocker.patch(
        "httpx.AsyncClient.post",
        side_effect=HTTPStatusError(
            "Token request failed",
            request=mocker.Mock(),
            response=mocker.Mock(status_code=400),
        ),
    )
    with pytest.raises(HTTPException) as exc_info:
        await GoogleOAuthService.process_google_login("invalid_code", mock_session)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
