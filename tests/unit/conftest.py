import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.core.config import get_test_settings
from app.models.room import Room
from app.models.room_user import RoomUser
from app.models.user import User


@pytest_asyncio.fixture
async def test_db_session() -> AsyncSession:
    test_settings = get_test_settings()
    engine = create_async_engine(
        test_settings.database_uri,
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()

    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))

    await engine.dispose()


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
async def test_room(test_db_session, test_user) -> Room:
    room = Room(
        name="Test Room",
        room_number="TEST123",
        max_users=4,
        is_playing=False,
        host_id=test_user.id,
    )

    test_db_session.add(room)
    await test_db_session.commit()
    await test_db_session.refresh(room)

    return room


@pytest_asyncio.fixture
async def test_room_user(test_db_session, test_room, test_user) -> RoomUser:
    room_user = RoomUser(
        room_id=test_room.id,
        user_id=test_user.id,
        is_ready=True,
    )

    test_db_session.add(room_user)
    await test_db_session.commit()
    await test_db_session.refresh(room_user)

    return room_user
