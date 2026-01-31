from sqlalchemy import Integer, String, TIMESTAMP, func, ForeignKey, DECIMAL, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class CommissionPayment(Base):
    __tablename__ = "commission_payments"

    __table_args__ = (
        UniqueConstraint("ride_id", "user_id", "is_refund", name="uq_commission_payment_ride_user_refund"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ride_id: Mapped[int] = mapped_column(ForeignKey("rides.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    amount: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="RUB")

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CREATED")

    tochka_operation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payment_link: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    purpose: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_mode: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    paid_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    transaction_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    is_refund: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())
    updated_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())

    ride = relationship("Ride")
    user = relationship("User")
