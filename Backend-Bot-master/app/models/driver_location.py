from sqlalchemy import Integer, String, TIMESTAMP, func, DECIMAL, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class DriverLocation(Base):
    __tablename__ = 'driver_locations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    driver_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey('driver_profiles.id'), nullable=False)
    latitude: Mapped[float | None] = mapped_column(DECIMAL(12, 8), nullable=True)
    longitude: Mapped[float | None] = mapped_column(DECIMAL(12, 8), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='offline')
    last_seen_at = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())

    driver_profile = relationship('DriverProfile')
