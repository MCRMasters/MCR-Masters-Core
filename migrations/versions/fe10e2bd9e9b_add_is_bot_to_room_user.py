"""add is_bot to room_user

Revision ID: fe10e2bd9e9b
Revises: 55755405d24c
Create Date: 2025-05-23 04:15:12.436159

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "fe10e2bd9e9b"
down_revision: Union[str, None] = "55755405d24c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "room_user",
        sa.Column("is_bot", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("room_user", "is_bot", server_default=None)


def downgrade() -> None:
    op.drop_column("room_user", "is_bot")
