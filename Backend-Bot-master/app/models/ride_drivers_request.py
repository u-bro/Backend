from sqlalchemy import BigInteger, String, TIMESTAMP, func, ForeignKey, DECIMAL, CheckConstraint, Index, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class RideDriversRequest(Base):
    __tablename__ = 'ride_drivers_requests'
    __table_args__ = (
        Index(
            "uq_ride_requests_pending_pair",
            "ride_id",
            "driver_profile_id",
            unique=True,
            postgresql_where=text("status = 'requested'"),
        ),
        Index(
            "ix_ride_requests_driver_requested_newest",
            "driver_profile_id",
            text("created_at DESC"),
            text("id DESC"),
            postgresql_where=text("status = 'requested'"),
        ),
        CheckConstraint(
            "removal_reason IS NULL OR "
            "(status = 'rejected' AND removal_reason = 'selected_other_driver') OR "
            "(status = 'canceled' AND removal_reason IN "
            "('ride_canceled', 'ride_expired', 'driver_withdrawn', 'driver_offline', 'driver_assigned_elsewhere'))",
            name="ck_ride_request_status_removal_reason",
        ),
        Index(
            "ix_ride_requests_ride_requested",
            "ride_id",
            postgresql_where=text("status = 'requested'"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ride_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey('rides.id'), nullable=True)
    driver_profile_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('driver_profiles.id'), nullable=False)
    car_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('cars.id'), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    eta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    offer_fare: Mapped[float | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    commission_amount: Mapped[float | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    removal_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())
    updated_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())

    ride = relationship('Ride', foreign_keys=[ride_id])
    driver_profile = relationship("DriverProfile", foreign_keys=[driver_profile_id])
    car = relationship("Car", foreign_keys=[car_id])
