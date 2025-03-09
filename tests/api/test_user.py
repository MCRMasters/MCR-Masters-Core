import pytest
from fastapi import status

from app.core.error import DomainErrorCode, MCRDomainError


@pytest.mark.asyncio
async def test_update_nickname_success(login_client, mock_user):
    mock_user.nickname = ""

    response = await login_client.put(
        "/api/v1/user/me/nickname",
        json={"nickname": "새닉네임"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["nickname"] == "새닉네임"
    assert data["uid"] == mock_user.uid
    assert data["email"] == mock_user.email


@pytest.mark.asyncio
async def test_update_nickname_already_set(login_client, mock_user, mocker):
    mock_user.nickname = "기존닉네임"

    mocker.patch(
        "app.services.auth.user_service.update_nickname",
        side_effect=MCRDomainError(
            code=DomainErrorCode.NICKNAME_ALREADY_SET,
            message="Nickname already set and cannot be changed",
            details={
                "user_id": str(mock_user.id),
                "current_nickname": mock_user.nickname,
            },
        ),
    )

    response = await login_client.put(
        "/api/v1/user/me/nickname",
        json={"nickname": "새닉네임"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == DomainErrorCode.NICKNAME_ALREADY_SET.value
    assert "기존닉네임" in data["error_details"]["current_nickname"]


@pytest.mark.asyncio
async def test_update_nickname_validation_error(login_client):
    response = await login_client.put(
        "/api/v1/user/me/nickname",
        json={"nickname": ""},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    response = await login_client.put(
        "/api/v1/user/me/nickname",
        json={"nickname": "1234567890123"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_update_nickname_unauthorized(client):
    response = await client.put(
        "/api/v1/user/me/nickname",
        json={"nickname": "새닉네임"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
