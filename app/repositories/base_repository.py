from abc import ABC
from typing import Generic, TypeVar, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, select

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T], ABC):
    def __init__(self, session: AsyncSession, model_class: type[T]):
        self.session = session
        self.model_class = model_class

    async def get_by_uuid(self, uuid: UUID) -> T | None:
        result = await self.session.execute(
            select(self.model_class).where(self.model_class.id == uuid),
        )
        return cast(T | None, result.scalar_one_or_none())

    async def get_all(self) -> list[T]:
        result = await self.session.execute(select(self.model_class))
        return cast(list[T], result.scalars().all())

    async def create(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, uuid: UUID) -> None:
        entity = await self.get_by_uuid(uuid)
        if entity:
            await self.session.delete(entity)
            await self.session.flush()
