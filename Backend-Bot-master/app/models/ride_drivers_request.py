from sqlalchemy import Integer, String, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class RideDriversRequest(Base):
    __tablename__ = 'ride_drivers_requests'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ride_id: Mapped[int] = mapped_column(Integer, ForeignKey('rides.id'), nullable=False)
    driver_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey('driver_profiles.id'), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    eta: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())
    updated_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())

    ride = relationship('Ride', foreign_keys=[ride_id])
    driver_profile = relationship("DriverProfile", foreign_keys=[driver_profile_id])
