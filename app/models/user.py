from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import Column, DateTime, String
from sqlmodel import Field, SQLModel

from app.models.time_stamp_mixin import TimeStampMixin
from app.util.validators import validate_uid


class UserStatus(str, Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    IN_LOBBY = "in-lobby"
    IN_ROOM = "in-room"
    IN_ROOM_READY = "in-room-ready"
    PLAYING = "playing"


class User(TimeStampMixin, SQLModel, table=True):  # type: ignore[call-arg]
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    uid: str = Field(unique=True)
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
