"""added admin seed

Revision ID: 9888bd599317
Revises: 0143e0f65bba
Create Date: 2025-12-17 17:15:14.022592

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os, hashlib


# revision identifiers, used by Alembic.
revision: str = '9888bd599317'
down_revision: Union[str, None] = '0143e0f65bba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_phone = os.getenv("ADMIN_PHONE")

    password_hash = hashlib.sha256(admin_password.encode()).hexdigest()

    # Create admin user (idempotent)
    bind.execute(
        sa.text(
            """
            INSERT INTO users (
                email,
                password_hash,
                username,
                phone,
                is_active,
                role_id,
                created_at,
                last_active_at
            )
            SELECT
                :email,
                :password_hash,
                :username,
                :phone,
                TRUE,
                r.id,
                NOW(),
                NOW()
            FROM roles r
            WHERE r.code = 'admin'
            ON CONFLICT (email) DO NOTHING
            """
        ),
        {
            "email": admin_email,
            "password_hash": password_hash,
            "username": admin_username,
            "phone": admin_phone,
        },
    )


def downgrade() -> None:
    bind = op.get_bind()

    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    bind.execute(sa.text("DELETE FROM users WHERE email = :email"), {"email": admin_email})

    bind.execute(sa.text("DELETE FROM roles WHERE code IN ('user', 'driver', 'admin')"))
