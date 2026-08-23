"""expand support workspace

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d8e9f0a1b2c3"
down_revision: Union[str, None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("support_conversations", sa.Column("source", sa.String(length=10), server_default="DIRECT", nullable=False))
    op.add_column("support_conversations", sa.Column("last_inbound_message_id", sa.BigInteger(), nullable=True))
    op.add_column("support_conversations", sa.Column("last_read_message_id", sa.BigInteger(), nullable=True))
    op.add_column("support_conversations", sa.Column("last_inbound_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("support_conversations", sa.Column("last_outbound_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("support_conversations", sa.Column("closed_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("support_conversations", sa.Column("closed_by", sa.String(length=150), nullable=True))
    op.create_check_constraint("ck_support_conversation_source", "support_conversations", "source IN ('APP', 'LANDING', 'DIRECT')")
    op.create_index("ix_support_conversations_queue", "support_conversations", ["status", "last_inbound_at"])

    op.alter_column("support_messages", "text", existing_type=sa.Text(), nullable=True)
    op.add_column("support_messages", sa.Column("message_type", sa.String(length=20), server_default="TEXT", nullable=False))
    op.add_column("support_messages", sa.Column("delivery_status", sa.String(length=10), server_default="RECEIVED", nullable=False))
    op.add_column("support_messages", sa.Column("delivery_error", sa.String(length=500), nullable=True))
    op.add_column("support_messages", sa.Column("idempotency_key", sa.String(length=100), nullable=True))
    op.add_column("support_messages", sa.Column("operator_name", sa.String(length=150), nullable=True))
    op.create_check_constraint(
        "ck_support_message_delivery_status",
        "support_messages",
        "delivery_status IN ('RECEIVED', 'PENDING', 'SENT', 'FAILED')",
    )
    op.create_unique_constraint("uq_support_messages_idempotency", "support_messages", ["conversation_id", "idempotency_key"])

    op.create_table(
        "support_message_attachments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.BigInteger(), nullable=False),
        sa.Column("attachment_type", sa.String(length=30), nullable=False),
        sa.Column("file_name", sa.String(length=500), nullable=True),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("provider_url", sa.Text(), nullable=True),
        sa.Column("provider_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["support_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_support_message_attachments_message_id", "support_message_attachments", ["message_id"])

    op.create_table(
        "support_entry_tokens",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("entry_metadata", sa.JSON(), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("consumed_max_user_id", sa.BigInteger(), nullable=True),
        sa.Column("consumed_max_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("source IN ('APP', 'LANDING')", name="ck_support_entry_token_source"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_support_entry_tokens_expires", "support_entry_tokens", ["expires_at"])

    op.execute(
        """
        WITH latest AS (
            SELECT DISTINCT ON (conversation_id) conversation_id, id, created_at
            FROM support_messages
            WHERE sender_type = 'USER'
            ORDER BY conversation_id, created_at DESC, id DESC
        )
        UPDATE support_conversations AS c
        SET last_inbound_message_id = latest.id,
            last_read_message_id = latest.id,
            last_inbound_at = latest.created_at
        FROM latest
        WHERE latest.conversation_id = c.id
        """
    )


def downgrade() -> None:
    op.drop_index("ix_support_entry_tokens_expires", table_name="support_entry_tokens")
    op.drop_table("support_entry_tokens")
    op.drop_index("ix_support_message_attachments_message_id", table_name="support_message_attachments")
    op.drop_table("support_message_attachments")
    op.drop_constraint("uq_support_messages_idempotency", "support_messages", type_="unique")
    op.drop_constraint("ck_support_message_delivery_status", "support_messages", type_="check")
    op.drop_column("support_messages", "operator_name")
    op.drop_column("support_messages", "idempotency_key")
    op.drop_column("support_messages", "delivery_error")
    op.drop_column("support_messages", "delivery_status")
    op.drop_column("support_messages", "message_type")
    op.execute("UPDATE support_messages SET text = '' WHERE text IS NULL")
    op.alter_column("support_messages", "text", existing_type=sa.Text(), nullable=False)
    op.drop_index("ix_support_conversations_queue", table_name="support_conversations")
    op.drop_constraint("ck_support_conversation_source", "support_conversations", type_="check")
    op.drop_column("support_conversations", "closed_by")
    op.drop_column("support_conversations", "closed_at")
    op.drop_column("support_conversations", "last_outbound_at")
    op.drop_column("support_conversations", "last_inbound_at")
    op.drop_column("support_conversations", "last_read_message_id")
    op.drop_column("support_conversations", "last_inbound_message_id")
    op.drop_column("support_conversations", "source")
