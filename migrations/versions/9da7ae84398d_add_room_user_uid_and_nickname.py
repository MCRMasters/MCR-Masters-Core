"""add room user uid and nickname

Revision ID: 9da7ae84398d
Revises: 26b53ee78bfa
Create Date: 2025-04-07 14:51:28.704795
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9da7ae84398d"
down_revision: Union[str, None] = "26b53ee78bfa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("roomuser", sa.Column("user_uid", sa.String(), nullable=False))
    op.add_column(
        "roomuser", sa.Column("user_nickname", sa.String(length=10), nullable=False)
    )

    op.create_foreign_key(
        "fk_roomuser_user_uid",
        "roomuser",
        "user",
        ["user_uid"],
        ["uid"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_roomuser_user_uid", "roomuser", type_="foreignkey")

    op.drop_column("roomuser", "user_nickname")
    op.drop_column("roomuser", "user_uid")
