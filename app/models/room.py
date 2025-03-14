from uuid import UUID, uuid4

from sqlalchemy import Column, Integer
from sqlmodel import Field, SQLModel

from app.models.time_stamp_mixin import TimeStampMixin


class Room(TimeStampMixin, SQLModel, table=True):  # type: ignore[call-arg]
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    name: str = Field(max_length=50)
    room_number: int = Field(
        sa_column=Column(
            Integer,
            autoincrement=True,
            unique=True,
            index=True,
            nullable=False,
        ),
    )
    max_users: int = Field(default=4)
    is_playing: bool = Field(default=False)
    host_id: UUID = Field(foreign_key="user.id")
