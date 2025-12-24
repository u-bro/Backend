from sqlalchemy import Integer, String, TIMESTAMP, func, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ride_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('rides.id'), nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sender_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    receiver_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    message_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    attachments = mapped_column(JSONB, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_moderated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at = mapped_column(TIMESTAMP, nullable=True, default=func.now())
    edited_at = mapped_column(TIMESTAMP, nullable=True)
    deleted_at = mapped_column(TIMESTAMP, nullable=True)

    ride = relationship('Ride')
    sender = relationship('User', foreign_keys=[sender_id])
    receiver = relationship('User', foreign_keys=[receiver_id])
