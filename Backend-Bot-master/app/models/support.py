from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, JSON, String, Text, TIMESTAMP, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SupportConversation(Base):
    __tablename__ = "support_conversations"
    __table_args__ = (
        CheckConstraint("status IN ('OPEN', 'CLOSED')", name="ck_support_conversation_status"),
        CheckConstraint("source IN ('APP', 'LANDING', 'DIRECT')", name="ck_support_conversation_source"),
        Index("ix_support_conversations_latest", "status", "updated_at"),
        Index("ix_support_conversations_queue", "status", "last_inbound_at"),
        Index("ix_support_conversations_open_max_chat", "max_chat_id", unique=True, postgresql_where=text("status = 'OPEN'")),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    max_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    max_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="OPEN", server_default="OPEN")
    source: Mapped[str] = mapped_column(String(10), nullable=False, default="DIRECT", server_default="DIRECT")
    last_inbound_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_read_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_inbound_at: Mapped[object | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_outbound_at: Mapped[object | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    closed_at: Mapped[object | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    closed_by: Mapped[str | None] = mapped_column(String(150), nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    user = relationship("User")
    messages = relationship("SupportMessage", back_populates="conversation", cascade="all, delete-orphan")


class SupportMessage(Base):
    __tablename__ = "support_messages"
    __table_args__ = (
        CheckConstraint("sender_type IN ('USER', 'OPERATOR', 'BOT')", name="ck_support_message_sender_type"),
        CheckConstraint("delivery_status IN ('RECEIVED', 'PENDING', 'SENT', 'FAILED')", name="ck_support_message_delivery_status"),
        UniqueConstraint("external_message_id", name="uq_support_messages_external_id"),
        UniqueConstraint("conversation_id", "idempotency_key", name="uq_support_messages_idempotency"),
        Index("ix_support_messages_conversation_created", "conversation_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("support_conversations.id", ondelete="CASCADE"), nullable=False)
    sender_type: Mapped[str] = mapped_column(String(10), nullable=False)
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message_type: Mapped[str] = mapped_column(String(20), nullable=False, default="TEXT", server_default="TEXT")
    delivery_status: Mapped[str] = mapped_column(String(10), nullable=False, default="RECEIVED", server_default="RECEIVED")
    delivery_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    operator_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    conversation = relationship("SupportConversation", back_populates="messages")
    user = relationship("User")
    attachments = relationship("SupportMessageAttachment", back_populates="message", cascade="all, delete-orphan")


class SupportMessageAttachment(Base):
    __tablename__ = "support_message_attachments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("support_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    attachment_type: Mapped[str] = mapped_column(String(30), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    provider_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    message = relationship("SupportMessage", back_populates="attachments")


class SupportEntryToken(Base):
    __tablename__ = "support_entry_tokens"
    __table_args__ = (
        CheckConstraint("source IN ('APP', 'LANDING')", name="ck_support_entry_token_source"),
        Index("ix_support_entry_tokens_expires", "expires_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    source: Mapped[str] = mapped_column(String(10), nullable=False)
    entry_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    expires_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    consumed_at: Mapped[object | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    consumed_max_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    consumed_max_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User")
