import pytest

from app.core.error import DomainErrorCode, MCRDomainError
from app.models.user import User


@pytest.mark.asyncio
async def test_generate_unique_uid(mock_user_service, mocker):
    mocker.patch(
        "app.repositories.user_repository.UserRepository.count",
        side_effect=[
            1,
            0,
        ],
    )

    generated_uid = await mock_user_service.generate_unique_uid()

    assert len(generated_uid) == 9
    assert generated_uid.isdigit()


@pytest.mark.asyncio
async def test_generate_unique_uid_failure(mock_user_service, mocker):
    mocker.patch(
        "app.repositories.user_repository.UserRepository.count",
        return_value=1,
    )

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_user_service.generate_unique_uid()

    assert exc_info.value.code == DomainErrorCode.UID_CREATE_FAILED


@pytest.mark.asyncio
async def test_get_or_create_user_new(mock_user_service, mocker):
    user_info = {"email": "new@example.com"}

    mocker.patch(
        "app.repositories.user_repository.UserRepository.filter_one",
        return_value=None,
    )

    new_uid = "987654321"
    mocker.patch(
        "app.services.auth.user_service.UserService.generate_unique_uid",
        return_value=new_uid,
    )

    new_user = User(uid=new_uid, email=user_info["email"], nickname="")
    mocker.patch(
        "app.repositories.user_repository.UserRepository.create",
        return_value=new_user,
    )

    user, is_new_user = await mock_user_service.get_or_create_user(user_info)

    assert is_new_user is True
    assert user.email == user_info["email"]
    assert user.uid == new_uid
    assert user.nickname == ""


@pytest.mark.asyncio
async def test_get_or_create_user_existing(mock_user_service, mocker):
    user_info = {"email": "existing@example.com"}
    existing_user = User(
        uid="123456789",
        email=user_info["email"],
        nickname="ExistingUser",
    )

    mocker.patch(
        "app.repositories.user_repository.UserRepository.filter_one",
        return_value=existing_user,
    )

    user, is_new_user = await mock_user_service.get_or_create_user(user_info)

    assert is_new_user is False
    assert user.email == existing_user.email
    assert user.uid == existing_user.uid
    assert user.nickname == existing_user.nickname


@pytest.mark.asyncio
async def test_get_or_create_user_existing_empty_nickname(mock_user_service, mocker):
    user_info = {"email": "new@example.com"}
    existing_user = User(
        uid="123456789",
        email=user_info["email"],
        nickname="",
    )

    mocker.patch(
        "app.repositories.user_repository.UserRepository.filter_one",
        return_value=existing_user,
    )

    user, is_new_user = await mock_user_service.get_or_create_user(user_info)

    assert is_new_user is True
    assert user.email == existing_user.email
    assert user.uid == existing_user.uid
    assert user.nickname == ""


@pytest.mark.asyncio
async def test_update_nickname_success(mock_user_service, user_id, mocker):
    user = User(id=user_id, uid="123456789", nickname="")
    new_nickname = "NewName"
    mocker.patch(
        "app.repositories.user_repository.UserRepository.get_by_uuid",
        return_value=user,
    )

    updated_user = User(id=user_id, uid="123456789", nickname=new_nickname)
    mocker.patch(
        "app.repositories.user_repository.UserRepository.update",
        return_value=updated_user,
    )

    result = await mock_user_service.update_nickname(user_id, new_nickname)

    assert result.nickname == new_nickname


@pytest.mark.asyncio
async def test_update_nickname_user_not_found(mock_user_service, user_id, mocker):
    mocker.patch(
        "app.repositories.user_repository.UserRepository.get_by_uuid",
        return_value=None,
    )

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_user_service.update_nickname(user_id, "NoName")

    assert exc_info.value.code == DomainErrorCode.USER_NOT_FOUND
    assert str(user_id) in exc_info.value.message


@pytest.mark.asyncio
async def test_update_nickname_already_set(mock_user_service, user_id, mocker):
    user = User(id=user_id, uid="123456789", nickname="ExistName")

    mocker.patch(
        "app.repositories.user_repository.UserRepository.get_by_uuid",
        return_value=user,
    )

    with pytest.raises(MCRDomainError) as exc_info:
        await mock_user_service.update_nickname(user_id, "NewName")

    assert exc_info.value.code == DomainErrorCode.NICKNAME_ALREADY_SET
    assert user.nickname in exc_info.value.details["current_nickname"]


@pytest.mark.asyncio
async def test_get_user_by_id(mock_user_service, user_id, mocker):
    user = User(
        id=user_id, uid="123456789", nickname="TestUser", email="test@example.com"
    )

    mocker.patch(
        "app.repositories.user_repository.UserRepository.filter_one",
        return_value=user,
    )

    # 테스트 대상 함수 호출
    result = await mock_user_service.get_user_by_id(user_id)

    # 검증
    assert result is not None
    assert result.id == user_id
    assert result.uid == "123456789"
    assert result.nickname == "TestUser"

    mock_user_service.user_repository.filter_one.assert_called_once_with(id=user_id)
