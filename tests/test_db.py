import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.core.config import get_test_settings


@pytest_asyncio.fixture
async def test_engine():
    test_settings = get_test_settings()
    engine = create_async_engine(
        test_settings.database_uri,
        echo=False,
        future=True,
        poolclass=NullPool,
    )

    # 테이블 생성 전에 기존 테이블 삭제 (CASCADE 옵션 사용)
    async with engine.begin() as conn:
        # 기존 테이블을 모두 삭제 (CASCADE 옵션 사용)
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))

        # 이제 새로운 테이블 생성
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # 테스트 후 정리
    async with engine.begin() as conn:
        # CASCADE 옵션으로 모든 테이블을 안전하게 제거
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


async def test_db_connection(test_db_session: AsyncSession):
    result = await test_db_session.execute(text("SELECT 1"))
    value = result.scalar()

    assert value == 1


async def test_transaction_rollback(test_db_session: AsyncSession):
    await test_db_session.execute(
        text("CREATE TABLE IF NOT EXISTS test_table (id INT)"),
    )
    await test_db_session.execute(text("INSERT INTO test_table (id) VALUES (1)"))
    await test_db_session.commit()

    result = await test_db_session.execute(text("SELECT COUNT(*) FROM test_table"))
    assert result.scalar() == 1

    await test_db_session.execute(text("INSERT INTO test_table (id) VALUES (2)"))
    await test_db_session.rollback()

    result = await test_db_session.execute(text("SELECT COUNT(*) FROM test_table"))
    assert result.scalar() == 1

    await test_db_session.execute(text("DROP TABLE test_table"))
    await test_db_session.commit()
