from sqlalchemy import BigInteger, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class DriverProfileModeration(Base):
    __tablename__ = "driver_profile_moderation"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    driver_profile_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("driver_profiles.id"), nullable=False)
    driver_moderation_info_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("driver_moderation_info.id"), nullable=False)
    created_at = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())