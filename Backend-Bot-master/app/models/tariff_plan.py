from sqlalchemy import Integer, String, TIMESTAMP, func, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base, metadata


class TariffPlan(Base):
    __tablename__ = 'tariff_plans'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    updated_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())
    created_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())
    effective_from: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), default=func.now())
    effective_to: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    base_fare: Mapped[float] = mapped_column(Float, nullable=False)
    rate_per_meter: Mapped[float] = mapped_column(Float, nullable=False)
    multiplier: Mapped[float] = mapped_column(Float, nullable=False)
    rules: Mapped[JSONB | None] = mapped_column(JSONB, nullable=True)
    commission_percentage: Mapped[float] = mapped_column(Float, nullable=False)
