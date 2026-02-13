"""added admin seed

Revision ID: 9888bd599317
Revises: 0143e0f65bba
Create Date: 2025-12-17 17:15:14.022592

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os


# revision identifiers, used by Alembic.
revision: str = '9888bd599317'
down_revision: Union[str, None] = '0143e0f65bba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    admin_phone = os.getenv("ADMIN_PHONE")

    bind.execute(
        sa.text(
            """
            INSERT INTO users (
                phone,
                is_active,
                role_id,
                created_at,
                last_active_at
            )
            SELECT
                :phone,
                TRUE,
                r.id,
                NOW(),
                NOW()
            FROM roles r
            WHERE r.code = 'admin'
            ON CONFLICT (phone) DO NOTHING
            """
        ),
        {
            "phone": admin_phone,
        },
    )


def downgrade() -> None:
    bind = op.get_bind()

    admin_phone = os.getenv("ADMIN_PHONE")
    bind.execute(sa.text("DELETE FROM users WHERE phone = :phone"), {"phone": admin_phone})
