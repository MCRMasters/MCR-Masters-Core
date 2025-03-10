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
    # 1단계: 임시 테이블 생성 (기존 데이터 저장용)
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

    # 2단계: 기존 데이터를 임시 테이블로 복사
    op.execute(
        "INSERT INTO roomuser_temp SELECT room_id, user_id, is_ready FROM roomuser"
    )

    # 3단계: 기존 테이블 삭제
    op.drop_table("roomuser")

    # 4단계: 새로운 테이블 생성 (UUID 추가)
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

    # 5단계: 임시 테이블에서 데이터 복원 (새로운 UUID 생성)
    op.execute(
        "INSERT INTO roomuser (id, room_id, user_id, is_ready) "
        "SELECT gen_random_uuid(), room_id, user_id, is_ready FROM roomuser_temp"
    )

    # 6단계: 임시 테이블 삭제
    op.drop_table("roomuser_temp")


def downgrade() -> None:
    # 1단계: 임시 테이블 생성 (기존 데이터 저장용)
    op.create_table(
        "roomuser_temp",
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("is_ready", sa.Boolean(), nullable=False),
    )

    # 2단계: 기존 데이터를 임시 테이블로 복사 (UUID 제외)
    op.execute(
        "INSERT INTO roomuser_temp SELECT room_id, user_id, is_ready FROM roomuser"
    )

    # 3단계: 기존 테이블 삭제
    op.drop_table("roomuser")

    # 4단계: 원래 테이블 스키마로 복원
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

    # 5단계: 임시 테이블에서 데이터 복원
    op.execute(
        "INSERT INTO roomuser (room_id, user_id, is_ready) "
        "SELECT room_id, user_id, is_ready FROM roomuser_temp"
    )

    # 6단계: 임시 테이블 삭제
    op.drop_table("roomuser_temp")
