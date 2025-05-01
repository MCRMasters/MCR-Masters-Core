import pytest
from fastapi import status

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.user import User

# TODO
pytestmark = pytest.mark.skip(reason="모든 테스트 스킵")


@pytest.mark.asyncio
async def test_update_nickname_success(login_client, mock_user):
    client, mocks = login_client
    mock_user.nickname = ""

    updated_user = User(
        id=mock_user.id, uid=mock_user.uid, email=mock_user.email, nickname="nickname"
    )
    mocks["services"]["user_service"].update_nickname.return_value = updated_user

    response = await client.put(
        "/api/v1/user/me/nickname",
        json={"nickname": "nickname"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Nickname Update Success"

    mocks["services"]["user_service"].update_nickname.assert_called_once_with(
        mock_user.id, "nickname"
    )


@pytest.mark.asyncio
async def test_update_nickname_already_set(login_client, mock_user):
    client, mocks = login_client
    mock_user.nickname = "nickname"

    error = MCRDomainError(
        code=DomainErrorCode.NICKNAME_ALREADY_SET,
        message="Nickname already set and cannot be changed",
        details={
            "user_id": str(mock_user.id),
            "current_nickname": mock_user.nickname,
        },
    )
    mocks["services"]["user_service"].update_nickname.side_effect = error

    response = await client.put(
        "/api/v1/user/me/nickname",
        json={"nickname": "nickname"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == DomainErrorCode.NICKNAME_ALREADY_SET.value
    assert "nickname" in data["error_details"]["current_nickname"]

    mocks["services"]["user_service"].update_nickname.assert_called_once_with(
        mock_user.id, "nickname"
    )


@pytest.mark.asyncio
async def test_update_nickname_unauthorized(client):
    client_instance, _ = client

    response = await client_instance.put(
        "/api/v1/user/me/nickname",
        json={"nickname": "nickname"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_current_user_info(login_client, mock_user):
    client, _ = login_client

    response = await client.get("/api/v1/user/me")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["uid"] == mock_user.uid
    assert data["nickname"] == mock_user.nickname
    assert data["email"] == mock_user.email
