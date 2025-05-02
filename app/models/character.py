from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from app.models.time_stamp_mixin import TimeStampMixin
from app.models.user_character import UserCharacter

if TYPE_CHECKING:
    from app.models.user import User


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
    owners: list[User] = Relationship(
        back_populates="owned_characters",
        link_model=UserCharacter,
    )
