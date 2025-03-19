import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.core.config import get_test_settings
from app.models.room import Room
from app.models.room_user import RoomUser
from app.models.user import User
from app.repositories.room_repository import RoomRepository
from app.repositories.room_user_repository import RoomUserRepository
from app.repositories.user_repository import UserRepository
from app.services.auth.google import GoogleOAuthService
from app.services.auth.user_service import UserService
from app.services.room_service import RoomService


@pytest_asyncio.fixture
async def test_engine():
    test_settings = get_test_settings()
    engine = create_async_engine(
        test_settings.database_uri,
        echo=False,
        future=True,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))

    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_engine) -> AsyncSession:
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


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


@pytest_asyncio.fixture
async def test_host(test_db_session) -> User:
    host = User(
        uid="987654321",
        nickname="HostUser",
        email="host@example.com",
    )

    test_db_session.add(host)
    await test_db_session.commit()
    await test_db_session.refresh(host)

    return host


@pytest_asyncio.fixture
async def test_room(test_db_session, test_host) -> Room:
    room = Room(
        name="테스트 방",
        room_number=123,
        max_users=4,
        is_playing=False,
        host_id=test_host.id,
    )

    test_db_session.add(room)
    await test_db_session.commit()
    await test_db_session.refresh(room)

    return room


@pytest_asyncio.fixture
async def test_playing_room(test_db_session, test_host) -> Room:
    room = Room(
        name="진행 중인 방",
        room_number=456,
        max_users=4,
        is_playing=True,
        host_id=test_host.id,
    )

    test_db_session.add(room)
    await test_db_session.commit()
    await test_db_session.refresh(room)

    return room


@pytest_asyncio.fixture
async def test_room_users(test_db_session, test_room, test_host) -> list[RoomUser]:
    users = [
        User(
            uid=f"100000{i}",
            nickname=f"TestUser{i}",
            email=f"test{i}@example.com",
        )
        for i in range(3)
    ]

    test_db_session.add_all(users)
    await test_db_session.commit()

    for user in users:
        await test_db_session.refresh(user)

    room_users = [
        RoomUser(
            room_id=test_room.id,
            user_id=user.id,
            is_ready=(i == 0),
        )
        for i, user in enumerate([*users, test_host])
    ]

    test_db_session.add_all(room_users)
    await test_db_session.commit()

    for room_user in room_users:
        await test_db_session.refresh(room_user)

    return room_users


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def room_id():
    return uuid.uuid4()


@pytest.fixture
def mock_session(mocker, test_user):
    session = mocker.AsyncMock()
    mock_result = mocker.Mock()
    mock_result.scalar_one_or_none.return_value = test_user
    session.execute = mocker.AsyncMock(return_value=mock_result)
    return session


@pytest.fixture
def mock_user_repository(mock_session, test_user):
    repository = UserRepository(mock_session)
    return repository


@pytest.fixture
def mock_room_repository(mock_session):
    repository = RoomRepository(mock_session)
    return repository


@pytest.fixture
def mock_room_user_repository(mock_session):
    repository = RoomUserRepository(mock_session)
    return repository


@pytest.fixture
def mock_user_service(mock_session, mock_user_repository):
    service = UserService(mock_session, mock_user_repository)
    return service


@pytest.fixture
def mock_google_service(mock_session, mock_user_service):
    service = GoogleOAuthService(mock_session, mock_user_service)
    return service


@pytest.fixture
def mock_room_service(
    mock_session,
    mock_room_repository,
    mock_room_user_repository,
    mock_user_repository,
):
    service = RoomService(
        session=mock_session,
        room_repository=mock_room_repository,
        room_user_repository=mock_room_user_repository,
        user_repository=mock_user_repository,
    )
    return service
