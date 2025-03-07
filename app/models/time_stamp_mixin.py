from datetime import UTC, datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import Mapped, declared_attr


class TimeStampMixin:
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:  # noqa: N805
        return Column(
            DateTime(timezone=True),
            default=datetime.now(UTC),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:  # noqa: N805
        return Column(
            DateTime(timezone=True),
            default=None,
            nullable=True,
            onupdate=datetime.now(UTC),
        )
