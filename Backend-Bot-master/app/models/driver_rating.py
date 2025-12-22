from sqlalchemy import Integer, String, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class DriverRating(Base):
    __tablename__ = 'driver_ratings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    driver_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey('driver_profiles.id'), nullable=False)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    ride_id: Mapped[int] = mapped_column(Integer, ForeignKey('rides.id'), nullable=False)
    rate: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at = mapped_column(TIMESTAMP, nullable=True, default=func.now())

    driver_profile = relationship('DriverProfile')
    ride = relationship('Ride')
    client = relationship('User')
