from sqlalchemy import BigInteger, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class DriverModerationInfo(Base):
    __tablename__ = 'driver_moderation_info'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())

    driver_profiles = relationship("DriverProfile", secondary="driver_profile_moderation", back_populates="moderation_info")
