from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel


class RoomUser(SQLModel, table=True):  # type: ignore[call-arg]
    room_id: UUID = Field(foreign_key="room.id", primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", primary_key=True)

    joined_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True)),
    )
    is_host: bool = Field(default=False)

    __table_args__ = (UniqueConstraint("user_id"),)
