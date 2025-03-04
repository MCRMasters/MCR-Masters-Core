from datetime import datetime
from enum import Enum

from pydantic import field_validator
from sqlalchemy import Column, DateTime, String
from sqlmodel import Field, SQLModel

from app.models.time_stamp_mixin import TimeStampMixin
from app.util.validators import validate_uid


class UserStatus(str, Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    IN_ROOM = "in-room"
    PLAYING = "playing"


class User(SQLModel, TimeStampMixin, table=True):  # type: ignore[call-arg]
    uid: str = Field(primary_key=True)
    nickname: str = Field(max_length=10)
    is_active: bool = Field(default=True)
    status: UserStatus = Field(default=UserStatus.OFFLINE, sa_column=Column(String(20)))

    last_login: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    email: str | None = Field(default=None)

    @field_validator("uid")
    @classmethod
    def validate_uid(cls, v: str) -> str:
        return validate_uid(v)
