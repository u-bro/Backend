from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String, Text, TIMESTAMP, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SupportConversation(Base):
    __tablename__ = "support_conversations"
    __table_args__ = (
        CheckConstraint("status IN ('OPEN', 'CLOSED')", name="ck_support_conversation_status"),
        Index("ix_support_conversations_latest", "status", "updated_at"),
        Index("ix_support_conversations_open_max_chat", "max_chat_id", unique=True, postgresql_where=text("status = 'OPEN'")),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    max_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    max_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="OPEN", server_default="OPEN")
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    user = relationship("User")
    messages = relationship("SupportMessage", back_populates="conversation", cascade="all, delete-orphan")


class SupportMessage(Base):
    __tablename__ = "support_messages"
    __table_args__ = (
        CheckConstraint("sender_type IN ('USER', 'OPERATOR', 'BOT')", name="ck_support_message_sender_type"),
        UniqueConstraint("external_message_id", name="uq_support_messages_external_id"),
        Index("ix_support_messages_conversation_created", "conversation_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("support_conversations.id", ondelete="CASCADE"), nullable=False)
    sender_type: Mapped[str] = mapped_column(String(10), nullable=False)
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    external_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    conversation = relationship("SupportConversation", back_populates="messages")
    user = relationship("User")
