from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.time_stamp_mixin import TimeStampMixin


class RoomUser(TimeStampMixin, SQLModel, table=True):  # type: ignore[call-arg]
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    room_id: UUID = Field(foreign_key="room.id")
    user_id: UUID = Field(foreign_key="user.id")
    user_uid: str
    user_nickname: str
    is_ready: bool = Field(default=False)
    slot_index: int = Field(default=0)

    __table_args__ = (UniqueConstraint("user_id"),)
