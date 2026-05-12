from sqlalchemy import BigInteger, Integer, String, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class DriverRating(Base):
    __tablename__ = 'driver_ratings'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    driver_profile_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('driver_profiles.id'), nullable=False)
    client_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True)
    ride_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey('rides.id'), nullable=True)
    rate: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())

    driver_profile = relationship('DriverProfile')
    ride = relationship('Ride', foreign_keys=[ride_id], back_populates='driver_rating')
    client = relationship('User')
