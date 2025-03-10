from uuid import uuid4

import pytest

from app.models.user import User
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_get_by_uuid(test_db_session):
    user_id = uuid4()
    user = User(
        id=user_id,
        uid="123456789",
        nickname="TestUser",
        email="test@example.com",
    )

    test_db_session.add(user)
    await test_db_session.commit()

    repo = UserRepository(test_db_session)
    result = await repo.get_by_uuid(user_id)

    assert result is not None
    assert result.id == user_id
    assert result.email == "test@example.com"
    assert result.nickname == "TestUser"


@pytest.mark.asyncio
async def test_get_by_email(test_db_session):
    email = "email-test@example.com"
    user = User(
        uid="123456788",
        nickname="EmailTest",
        email=email,
    )

    test_db_session.add(user)
    await test_db_session.commit()

    repo = UserRepository(test_db_session)
    result = await repo.get_by_email(email)

    assert result is not None
    assert result.email == email
    assert result.nickname == "EmailTest"


@pytest.mark.asyncio
async def test_get_by_uid(test_db_session):
    uid = "987654321"
    user = User(
        uid=uid,
        nickname="UidTest",
        email="uid-test@example.com",
    )

    test_db_session.add(user)
    await test_db_session.commit()

    repo = UserRepository(test_db_session)
    result = await repo.get_by_uid(uid)

    assert result is not None
    assert result.uid == uid
    assert result.nickname == "UidTest"


@pytest.mark.asyncio
async def test_create_user(test_db_session):
    user = User(
        uid="123456787",
        nickname="CreateTest",
        email="create-test@example.com",
    )

    repo = UserRepository(test_db_session)
    created_user = await repo.create(user)

    assert created_user.id is not None
    assert created_user.uid == "123456787"
    assert created_user.nickname == "CreateTest"

    result = await repo.get_by_email("create-test@example.com")
    assert result is not None
    assert result.id == created_user.id


@pytest.mark.asyncio
async def test_update_user(test_db_session):
    user = User(
        uid="123456786",
        nickname="Before",
        email="update-test@example.com",
    )

    test_db_session.add(user)
    await test_db_session.commit()

    user.nickname = "After"
    repo = UserRepository(test_db_session)
    updated_user = await repo.update(user)

    assert updated_user.nickname == "After"

    result = await repo.get_by_email("update-test@example.com")
    assert result is not None
    assert result.nickname == "After"


@pytest.mark.asyncio
async def test_delete_user(test_db_session):
    user = User(
        uid="123456785",
        nickname="DeleteTest",
        email="delete-test@example.com",
    )

    test_db_session.add(user)
    await test_db_session.commit()

    repo = UserRepository(test_db_session)
    await repo.delete(user.id)

    result = await repo.get_by_uuid(user.id)
    assert result is None
