import pytest
import pytest_asyncio

from app.models.user import User
from app.repositories.user_repository import UserRepository

# TODO
pytestmark = pytest.mark.skip(reason="모든 테스트 스킵")


@pytest_asyncio.fixture
async def test_user(test_db_session) -> User:
    user = User(
        uid="123456789",
        nickname="TestUser",
        email="test@example.com",
    )

    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)

    return user


@pytest.mark.asyncio
async def test_get_by_uuid(test_db_session, test_user):
    repo = UserRepository(test_db_session)
    result = await repo.get_by_uuid(test_user.id)

    assert result is not None
    assert result.id == test_user.id
    assert result.email == test_user.email
    assert result.nickname == test_user.nickname


@pytest.mark.asyncio
async def test_create_user(test_db_session):
    user = User(
        uid="987654321",
        nickname="CreateTest",
        email="create-test@example.com",
    )

    repo = UserRepository(test_db_session)
    created_user = await repo.create(user)

    assert created_user.id is not None
    assert created_user.uid == user.uid
    assert created_user.nickname == user.nickname


@pytest.mark.asyncio
async def test_update_user(test_db_session, test_user):
    test_user.nickname = "NewName"

    repo = UserRepository(test_db_session)
    updated_user = await repo.update(test_user)

    assert updated_user.nickname == "NewName"


@pytest.mark.asyncio
async def test_delete_user(test_db_session, test_user):
    repo = UserRepository(test_db_session)
    await repo.delete(test_user.id)

    result = await repo.get_by_uuid(test_user.id)
    assert result is None
