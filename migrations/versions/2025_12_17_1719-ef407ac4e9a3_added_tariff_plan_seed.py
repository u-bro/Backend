"""added tariff_plan seed

Revision ID: ef407ac4e9a3
Revises: 9888bd599317
Create Date: 2025-12-17 17:19:17.963437

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef407ac4e9a3'
down_revision: Union[str, None] = '9888bd599317'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:    
    op.execute("""
        INSERT INTO tariff_plans (name, effective_from, effective_to, base_fare, rate_per_meter, multiplier, commission_percentage)
        VALUES
        ('Standart', NOW(), NULL, 3.0, 0.5, 1.0, 5.0);
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM tariff_plans WHERE name = 'Standart'
    """)
