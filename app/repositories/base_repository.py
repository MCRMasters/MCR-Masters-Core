from abc import ABC
from typing import Any, Generic, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import BinaryExpression, Select
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

    async def get_by_uuid_with_options(
        self, uuid: UUID, *load_options: Any
    ) -> T | None:
        stmt: Select = (
            select(self.model_class)
            .options(*load_options)
            .where(self.model_class.id == uuid)
        )
        result = await self.session.execute(stmt)
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

    def _build_query(self, *filters: BinaryExpression, **kwargs: Any) -> Select:
        query = select(self.model_class)

        for filter_condition in filters:
            query = query.where(filter_condition)

        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                query = query.where(getattr(self.model_class, key) == value)

        return query

    async def filter(
        self,
        *filters: BinaryExpression,
        offset: int | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> list[T]:
        query = self._build_query(*filters, **kwargs)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def filter_one(self, *filters: BinaryExpression, **kwargs: Any) -> T | None:
        query = self._build_query(*filters, **kwargs)
        query = query.limit(1)

        result = await self.session.execute(query)
        return cast(T | None, result.scalar_one_or_none())

    async def filter_one_or_raise(self, *filters: BinaryExpression, **kwargs: Any) -> T:
        result = await self.filter_one(*filters, **kwargs)
        if not result:
            filter_details = {key: str(value) for key, value in kwargs.items()}
            raise MCRDomainError(
                code=self.not_found_error_code,
                message=f"{self.model_class.__name__} not found",
                details={
                    "model": self.model_class.__name__,
                    "filters": str(filters) if filters else None,
                    "conditions": filter_details,
                },
            )
        return result

    async def filter_with_options(
        self,
        *filters: BinaryExpression,
        load_options: list[Any] = [],
        offset: int | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> list[T]:
        query = self._build_query(*filters, **kwargs).options(*load_options)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, *filters: BinaryExpression, **kwargs: Any) -> int:
        query = select(func.count()).select_from(self.model_class)

        for filter_condition in filters:
            query = query.where(filter_condition)

        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                query = query.where(getattr(self.model_class, key) == value)

        result = await self.session.execute(query)
        return cast(int, result.scalar_one())
