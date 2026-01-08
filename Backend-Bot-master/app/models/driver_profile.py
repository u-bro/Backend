from sqlalchemy import Integer, String, TIMESTAMP, func, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class DriverProfile(Base):
    __tablename__ = 'driver_profiles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    birth_date = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    license_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    license_category: Mapped[str | None] = mapped_column(String(20), nullable=True)
    license_issued_at = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    license_expires_at = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_by: Mapped[int | None] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    qualification_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    classes_allowed = mapped_column(JSONB, nullable=False)
    current_class = mapped_column(String(50), nullable=True)
    documents_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    documents_review_notes: Mapped[str | None] = mapped_column(String, nullable=True)
    rating_avg = mapped_column(Integer, nullable=True)
    rating_count = mapped_column(Integer, nullable=True, default=0)
    ride_count = mapped_column(Integer, nullable=True, default=0)
    created_at = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())
    updated_at = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())

    user = relationship('User', back_populates="driver_profile", foreign_keys=[user_id])
    approved_by_user = relationship('User', foreign_keys=[approved_by])
