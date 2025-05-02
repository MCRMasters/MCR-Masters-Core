from uuid import UUID

from sqlmodel import Field, SQLModel

from app.models.time_stamp_mixin import TimeStampMixin


class UserCharacter(TimeStampMixin, SQLModel, table=True):  # type: ignore[call-arg]
    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    character_code: str = Field(
        foreign_key="character.code",
        primary_key=True,
        max_length=10,
    )
