from datetime import datetime
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from app.models.time_stamp_mixin import TimeStampMixin
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

    @field_validator("uid")
    @classmethod
    def validate_uid(cls, v: str) -> str:  # pragma: no cover
        return validate_uid(v)

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str) -> str:  # pragma: no cover
        return validate_nickname(v)
