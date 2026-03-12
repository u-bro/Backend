from sqlalchemy import BigInteger, String, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class DeviceToken(Base):
    __tablename__ = 'device_tokens'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False)
    platform: Mapped[str] = mapped_column(String, nullable=False)
    created_at = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())

    user = relationship('User')
