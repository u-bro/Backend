import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, DECIMAL, DateTime, ForeignKey, func
from app.db import Base, metadata


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_gpu_storage_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_gpu_storage.id"), nullable=False)

    price: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    gpu_storages = relationship("UserGpuStorage", back_populates="order")
