"""safe add is_registred to phone_verifications

Revision ID: f979e2435424
Revises: 503fad72d676
Create Date: 2025-12-27 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f979e2435424'
down_revision: Union[str, None] = '503fad72d676'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add column as nullable with server default false to avoid failing on existing NULLs
    op.add_column('phone_verifications', sa.Column('is_registred', sa.Boolean(), nullable=True, server_default=sa.text('false')))
    # Backfill any existing NULLs
    op.execute("UPDATE phone_verifications SET is_registred = false WHERE is_registred IS NULL;")
    # Make column NOT NULL
    op.alter_column('phone_verifications', 'is_registred', existing_type=sa.Boolean(), nullable=False)
    # Remove server default
    op.execute('ALTER TABLE phone_verifications ALTER COLUMN is_registred DROP DEFAULT;')


def downgrade() -> None:
    op.drop_column('phone_verifications', 'is_registred')
