"""added roles seed

Revision ID: 0143e0f65bba
Revises: d474883cbcea
Create Date: 2025-12-17 17:13:58.986758

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0143e0f65bba'
down_revision: Union[str, None] = 'd474883cbcea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO roles (code, name, description)
        VALUES
        ('user', 'User', 'Default user'),
        ('driver', 'Driver', 'Driver account'),
        ('admin', 'Admin', 'System administrator')
        ON CONFLICT (code) DO NOTHING;
    """)


def downgrade() -> None:
     op.execute("DELETE FROM roles WHERE code IN ('admin', 'user', 'driver')")

