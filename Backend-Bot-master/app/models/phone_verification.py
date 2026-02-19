from sqlalchemy import Integer, String, TIMESTAMP, func, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class PhoneVerification(Base):
    __tablename__ = 'phone_verifications'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    expires_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    next_sending_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_registred: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())

    user = relationship('User')
