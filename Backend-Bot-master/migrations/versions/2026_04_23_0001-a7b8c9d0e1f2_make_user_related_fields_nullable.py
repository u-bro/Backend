"""make user related fields nullable

Revision ID: a7b8c9d0e1f2
Revises: c9f7a1d2e3b4
Create Date: 2026-04-23 00:01:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "c9f7a1d2e3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "driver_profiles",
        "user_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )
    op.alter_column(
        "driver_ratings",
        "client_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )
    op.alter_column(
        "commission_payments",
        "user_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )
    op.alter_column(
        "ride_status_history",
        "changed_by",
        existing_type=sa.BigInteger(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "commission_payments",
        "user_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.alter_column(
        "driver_ratings",
        "client_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.alter_column(
        "driver_profiles",
        "user_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.alter_column(
        "ride_status_history",
        "changed_by",
        existing_type=sa.BigInteger(),
        nullable=False,
    )