"""add support conversations and messages

Revision ID: c7d8e9f0a1b2
Revises: 71daa819b571
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, None] = "71daa819b571"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "support_conversations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("max_user_id", sa.BigInteger(), nullable=True),
        sa.Column("max_chat_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=10), server_default="OPEN", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("status IN ('OPEN', 'CLOSED')", name="ck_support_conversation_status"),
    )
    op.create_index("ix_support_conversations_latest", "support_conversations", ["status", "updated_at"])
    op.create_index("ix_support_conversations_open_max_chat", "support_conversations", ["max_chat_id"], unique=True, postgresql_where=sa.text("status = 'OPEN'"))
    op.create_table(
        "support_messages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.BigInteger(), nullable=False),
        sa.Column("sender_type", sa.String(length=10), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("external_message_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["support_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_message_id", name="uq_support_messages_external_id"),
        sa.CheckConstraint("sender_type IN ('USER', 'OPERATOR', 'BOT')", name="ck_support_message_sender_type"),
    )
    op.create_index("ix_support_messages_conversation_created", "support_messages", ["conversation_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_support_messages_conversation_created", table_name="support_messages")
    op.drop_table("support_messages")
    op.drop_index("ix_support_conversations_open_max_chat", table_name="support_conversations")
    op.drop_index("ix_support_conversations_latest", table_name="support_conversations")
    op.drop_table("support_conversations")
