"""add uuid to roomuser

Revision ID: ${revision_id}
Revises: 66513b501de1
Create Date: ${create_date}

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "6302c9ac134c"
down_revision: Union[str, None] = "66513b501de1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roomuser_temp",
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("is_ready", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["room_id"],
            ["room.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
    )

    op.execute(
        "INSERT INTO roomuser_temp SELECT room_id, user_id, is_ready FROM roomuser"
    )

    op.drop_table("roomuser")

    op.create_table(
        "roomuser",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("is_ready", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["room_id"],
            ["room.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.execute(
        "INSERT INTO roomuser (id, room_id, user_id, is_ready) "
        "SELECT gen_random_uuid(), room_id, user_id, is_ready FROM roomuser_temp"
    )

    op.drop_table("roomuser_temp")


def downgrade() -> None:
    op.create_table(
        "roomuser_temp",
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("is_ready", sa.Boolean(), nullable=False),
    )

    op.execute(
        "INSERT INTO roomuser_temp SELECT room_id, user_id, is_ready FROM roomuser"
    )

    op.drop_table("roomuser")

    op.create_table(
        "roomuser",
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("is_ready", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["room_id"],
            ["room.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("room_id", "user_id"),
        sa.UniqueConstraint("user_id"),
    )

    op.execute(
        "INSERT INTO roomuser (room_id, user_id, is_ready) "
        "SELECT room_id, user_id, is_ready FROM roomuser_temp"
    )

    op.drop_table("roomuser_temp")
