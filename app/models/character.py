from __future__ import annotations

from typing import ClassVar
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from app.models.time_stamp_mixin import TimeStampMixin


class Character(TimeStampMixin, SQLModel, table=True):  # type: ignore[call-arg]
    DEFAULT_CHARACTER_CODE: ClassVar[str] = "c0"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    code: str = Field(
        default=DEFAULT_CHARACTER_CODE,
        max_length=10,
        unique=True,
        index=True,
    )
    name: str
