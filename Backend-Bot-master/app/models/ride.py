from sqlalchemy import Integer, String, TIMESTAMP, func, DECIMAL, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base, metadata


class Ride(Base):
    __tablename__ = 'rides'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    driver_profile_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('driver_profiles.id'), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pickup_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pickup_lat: Mapped[float] = mapped_column(DECIMAL(12, 8), nullable=False)
    pickup_lng: Mapped[float] = mapped_column(DECIMAL(12, 8), nullable=False)
    dropoff_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dropoff_lat: Mapped[float | None] = mapped_column(DECIMAL(12, 8), nullable=True)
    dropoff_lng: Mapped[float | None] = mapped_column(DECIMAL(12, 8), nullable=True)
    scheduled_at = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    started_at = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    canceled_at = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expected_fare: Mapped[float | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    expected_fare_snapshot = mapped_column(JSONB, nullable=True)
    driver_fare: Mapped[float | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    commission_amount: Mapped[float | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    actual_fare: Mapped[float | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    distance_meters: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_str: Mapped[str | None] = mapped_column(String(50), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_str: Mapped[str | None] = mapped_column(String(50), nullable=True)
    transaction_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('transactions.id'), nullable=True)
    commission_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('commissions.id'), nullable=True)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    anomaly_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ride_metadata = mapped_column(JSONB, nullable=True)
    created_at = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())
    updated_at = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())
    tariff_plan_id: Mapped[int] = mapped_column(Integer, ForeignKey('tariff_plans.id'))
    ride_class: Mapped[str] = mapped_column(Text, nullable=False)
    comment = mapped_column(Text, nullable=True)
    ride_type: Mapped[str] = mapped_column(Text, nullable=False)

    client = relationship('User', foreign_keys=[client_id])
    driver_profile = relationship('DriverProfile', foreign_keys=[driver_profile_id])
    driver_rating = relationship('DriverRating', foreign_keys='DriverRating.ride_id', back_populates='ride', uselist=False)
    tariff_plan = relationship('TariffPlan', foreign_keys=[tariff_plan_id])
