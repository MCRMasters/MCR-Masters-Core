from abc import ABC
from typing import Any, Generic, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import BinaryExpression
from sqlmodel import SQLModel

from app.core.error import DomainErrorCode, MCRDomainError

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T], ABC):
    def __init__(
        self,
        session: AsyncSession,
        model_class: type[T],
        not_found_error_code: DomainErrorCode,
    ):
        self.session = session
        self.model_class = model_class
        self.not_found_error_code = not_found_error_code

    async def get_by_uuid(self, uuid: UUID) -> T | None:
        result = await self.session.execute(
            select(self.model_class).where(self.model_class.id == uuid),
        )
        return cast(T | None, result.scalar_one_or_none())

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

    async def filter(
        self,
        *filters: BinaryExpression,
        offset: int | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> list[T]:
        query = select(self.model_class)

        for filter_condition in filters:
            query = query.where(filter_condition)

        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                query = query.where(getattr(self.model_class, key) == value)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def filter_one(self, *filters: BinaryExpression, **kwargs: Any) -> T | None:
        results = await self.filter(*filters, limit=1, **kwargs)
        return results[0] if results else None

    async def filter_one_or_raise(self, *filters: BinaryExpression, **kwargs: Any) -> T:
        result = await self.filter_one(*filters, limit=1, **kwargs)
        if not result:
            raise MCRDomainError(
                code=self.not_found_error_code,
                message=f"{self.model_class.__name__} not found",
                details={
                    "model": self.model_class.__name__,
                    "filters": str(filters) if filters else None,
                    "conditions": kwargs,
                },
            )
        return result

    async def count(self, *filters: BinaryExpression, **kwargs: Any) -> int:
        query = select(func.count()).select_from(self.model_class)

        for filter_condition in filters:
            query = query.where(filter_condition)

        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                query = query.where(getattr(self.model_class, key) == value)

        result = await self.session.execute(query)
        return cast(int, result.scalar_one())
