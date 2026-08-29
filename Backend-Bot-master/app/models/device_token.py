from sqlalchemy import BigInteger, CheckConstraint, String, TIMESTAMP, UniqueConstraint, func, ForeignKey
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class DeviceToken(Base):
    __tablename__ = 'device_tokens'
    __table_args__ = (
        UniqueConstraint('token', name='uq_device_tokens_token'),
        CheckConstraint("platform IN ('android', 'ios')", name='ck_device_tokens_platform'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False)
    platform: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=func.now())

    user = relationship('User')
