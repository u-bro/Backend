"""add admin push notification history

Revision ID: f1a2b3c4d5e6
Revises: e9f0a1b2c3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e9f0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_push_notifications",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("audience", sa.String(length=20), nullable=False),
        sa.Column("target_user_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("operator_id", sa.BigInteger(), nullable=False),
        sa.Column("operator_name", sa.String(length=150), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="processing", nullable=False),
        sa.Column("recipient_user_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("attempted_token_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("success_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failure_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("audience IN ('user', 'all')", name="ck_admin_push_audience"),
        sa.CheckConstraint("status IN ('processing', 'sent', 'partial', 'failed')", name="ck_admin_push_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_push_created_at", "admin_push_notifications", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_admin_push_created_at", table_name="admin_push_notifications")
    op.drop_table("admin_push_notifications")
