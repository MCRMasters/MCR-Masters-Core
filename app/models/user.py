from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.models.character import Character
from app.models.time_stamp_mixin import TimeStampMixin
from app.models.user_character import UserCharacter
from app.util.validators import validate_nickname, validate_uid


class User(TimeStampMixin, SQLModel, table=True):  # type: ignore[call-arg]
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    uid: str = Field(unique=True)
    nickname: str = Field(max_length=10)
    is_online: bool = Field(default=False)

    last_login: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    email: str | None = Field(default=None)

    character_code: str = Field(
        default=Character.DEFAULT_CHARACTER_CODE,
        foreign_key="character.code",
        max_length=10,
        index=True,
        nullable=False,
    )

    character: Character = Relationship(
        sa_relationship_kwargs={"foreign_keys": [character_code]}
    )

    owned_characters: list[Character] = Relationship(link_model=UserCharacter)

    @field_validator("uid")
    @classmethod
    def validate_uid(cls, v: str) -> str:  # pragma: no cover
        return validate_uid(v)

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str) -> str:  # pragma: no cover
        return validate_nickname(v)
