"""added commission seed

Revision ID: 573989f2c4d0
Revises: ec9f088cbc8e
Create Date: 2026-01-09 13:04:16.006875

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '573989f2c4d0'
down_revision: Union[str, None] = 'ec9f088cbc8e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO commissions (id, name, percentage, fixed_amount, currency, valid_from, valid_to, created_at)
        VALUES
        (1, 'Plan1', 5.0, 0, 'USD', '2026-01-01', '2026-12-31', NOW()),
        (2, 'Plan2', 0, 50, 'RUB', '2026-02-01', '2026-12-31', NOW());
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM commissions WHERE id IN (1, 2)
    """)
