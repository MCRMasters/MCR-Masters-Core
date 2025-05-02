"""Seed characters c1 through c5

Revision ID: 55755405d24c
Revises: a651a745199f
Create Date: 2025-05-02 07:09:59.829313

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "55755405d24c"
down_revision: Union[str, None] = "a651a745199f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from datetime import datetime, timezone
    import uuid
    import sqlalchemy as sa

    character_tbl = sa.table(
        "character",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("code", sa.String(length=10)),
        sa.column("name", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    op.bulk_insert(
        character_tbl,
        [
            {
                "id": uuid.uuid4(),
                "code": f"c{i}",
                "name": f"c{i}",
                "created_at": datetime.now(timezone.utc),
                "updated_at": None,
            }
            for i in range(1, 6)
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM character WHERE code IN ('c1','c2','c3','c4','c5')")
    )
