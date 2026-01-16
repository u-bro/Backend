"""added commission_payments table

Revision ID: a1b2c3d4e5f6
Revises: 13f46a5def4a
Create Date: 2026-01-15 16:59:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '13f46a5def4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'commission_payments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ride_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='RUB', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='CREATED', nullable=False),
        sa.Column('tochka_operation_id', sa.String(length=64), nullable=True),
        sa.Column('payment_link', sa.String(length=2048), nullable=True),
        sa.Column('purpose', sa.String(length=255), nullable=True),
        sa.Column('payment_mode', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('paid_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('payment_id', sa.String(length=128), nullable=True),
        sa.Column('transaction_id', sa.String(length=128), nullable=True),
        sa.Column('raw_request', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('raw_response', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_refund', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['ride_id'], ['rides.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tochka_operation_id'),
        sa.UniqueConstraint('ride_id', 'user_id', 'is_refund', name='uq_commission_payment_ride_user_refund'),
    )


def downgrade() -> None:
    op.drop_table('commission_payments')
