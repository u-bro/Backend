"""harden ride status values

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        DECLARE details text;
        BEGIN
          SELECT string_agg(format('ride=%s status=%s', id, coalesce(status, '<NULL>')), '; ' ORDER BY id)
          INTO details
          FROM rides
          WHERE status IS NULL OR status NOT IN (
            'requested', 'waiting_commission', 'accepted', 'on_the_way',
            'arrived', 'started', 'completed', 'canceled'
          );

          IF details IS NOT NULL THEN
            RAISE EXCEPTION 'Cannot harden rides.status; invalid rows: %', details;
          END IF;
        END $$;
        """
    )
    op.alter_column("rides", "status", existing_type=sa.String(length=50), nullable=False)
    op.create_check_constraint(
        "ck_rides_status_valid",
        "rides",
        "status IN ('requested','waiting_commission','accepted','on_the_way','arrived','started','completed','canceled')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_rides_status_valid", "rides", type_="check")
    op.alter_column("rides", "status", existing_type=sa.String(length=50), nullable=True)
