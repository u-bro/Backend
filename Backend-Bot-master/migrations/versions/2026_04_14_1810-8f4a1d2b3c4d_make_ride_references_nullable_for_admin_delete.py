"""make ride references nullable for admin delete

Revision ID: 8f4a1d2b3c4d
Revises: 431dd2161660
Create Date: 2026-04-14 18:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f4a1d2b3c4d'
down_revision = '431dd2161660'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('commission_payments', 'ride_id', existing_type=sa.BigInteger(), nullable=True)
    op.alter_column('ride_status_history', 'ride_id', existing_type=sa.BigInteger(), nullable=True)
    op.alter_column('ride_drivers_requests', 'ride_id', existing_type=sa.BigInteger(), nullable=True)
    op.alter_column('driver_ratings', 'ride_id', existing_type=sa.BigInteger(), nullable=True)


def downgrade() -> None:
    op.alter_column('driver_ratings', 'ride_id', existing_type=sa.BigInteger(), nullable=False)
    op.alter_column('ride_drivers_requests', 'ride_id', existing_type=sa.BigInteger(), nullable=False)
    op.alter_column('ride_status_history', 'ride_id', existing_type=sa.BigInteger(), nullable=False)
    op.alter_column('commission_payments', 'ride_id', existing_type=sa.BigInteger(), nullable=False)
