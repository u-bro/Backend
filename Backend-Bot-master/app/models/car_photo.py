from sqlalchemy import Integer, String, TIMESTAMP, func, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class CarPhoto(Base):
    __tablename__ = 'car_photos'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    car_id: Mapped[int] = mapped_column(Integer, ForeignKey('cars.id'), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())
    updated_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=func.now())

    car = relationship('Car', foreign_keys=[car_id])
