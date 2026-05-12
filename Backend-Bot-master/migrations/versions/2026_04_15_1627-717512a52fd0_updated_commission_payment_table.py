"""updated commission_payment table

Revision ID: 717512a52fd0
Revises: 8f4a1d2b3c4d
Create Date: 2026-04-15 16:27:38.290015

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '717512a52fd0'
down_revision: Union[str, None] = '8f4a1d2b3c4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('commission_payments', 'tochka_operation_id')
    op.drop_column('commission_payments', 'payment_mode')


def downgrade() -> None:
    op.add_column('commission_payments', sa.Column('tochka_operation_id', sa.String(length=64), nullable=True))
    op.add_column('commission_payments', sa.Column('payment_mode', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
