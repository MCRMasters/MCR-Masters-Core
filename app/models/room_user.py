from uuid import UUID

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class RoomUser(SQLModel, table=True):  # type: ignore[call-arg]
    room_id: UUID = Field(foreign_key="room.id", primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    is_host: bool = Field(default=False)
    is_ready: bool = Field(default=False)

    __table_args__ = (UniqueConstraint("user_id"),)
