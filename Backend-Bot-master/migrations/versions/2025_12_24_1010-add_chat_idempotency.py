"""add chat_messages idempotency_key

Revision ID: a1b2c3d4e5f6
Revises: ef407ac4e9a3
Create Date: 2025-12-24 10:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'ef407ac4e9a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add idempotency_key column and unique constraint
    op.add_column('chat_messages', sa.Column('idempotency_key', sa.String(length=64), nullable=True))
    op.create_index('ix_chat_messages_idempotency_key', 'chat_messages', ['idempotency_key'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_chat_messages_idempotency_key', table_name='chat_messages')
    op.drop_column('chat_messages', 'idempotency_key')
