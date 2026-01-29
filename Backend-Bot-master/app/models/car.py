from sqlalchemy import Integer, String, TIMESTAMP, func, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Car(Base):
    __tablename__ = 'cars'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    driver_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey('driver_profiles.id'), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=True)
    number: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())
    updated_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())

    driver_profile = relationship('DriverProfile', foreign_keys=[driver_profile_id], back_populates="cars")