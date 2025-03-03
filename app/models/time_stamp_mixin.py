from datetime import UTC, datetime

from sqlalchemy import Column, DateTime
from sqlmodel import Field


class TimeStampMixin:
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=True,
            onupdate=datetime.now(UTC),
        ),
    )
