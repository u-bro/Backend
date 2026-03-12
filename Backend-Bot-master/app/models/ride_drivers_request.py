from sqlalchemy import BigInteger, String, TIMESTAMP, func, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class RideDriversRequest(Base):
    __tablename__ = 'ride_drivers_requests'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ride_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('rides.id'), nullable=False)
    driver_profile_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('driver_profiles.id'), nullable=False)
    car_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('cars.id'), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    eta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    offer_fare: Mapped[float | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    commission_amount: Mapped[float | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    created_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())
    updated_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())

    ride = relationship('Ride', foreign_keys=[ride_id])
    driver_profile = relationship("DriverProfile", foreign_keys=[driver_profile_id])
    car = relationship("Car", foreign_keys=[car_id])
