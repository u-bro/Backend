from sqlalchemy import BigInteger, String, TIMESTAMP, func, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class RideStatusHistory(Base):
    __tablename__ = 'ride_status_history'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ride_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('rides.id'), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    changed_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta = mapped_column(JSONB, nullable=True)
    created_at = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())

    ride = relationship('Ride')
