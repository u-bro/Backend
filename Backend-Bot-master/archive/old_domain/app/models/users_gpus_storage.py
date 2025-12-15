from sqlalchemy import Integer, ForeignKey, func, TIMESTAMP, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base, metadata


class UserGpuStorage(Base):
    __tablename__ = "user_gpu_storage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    gpu_id: Mapped[int] = mapped_column(ForeignKey("gpus.id"), nullable=False)
    added_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, nullable=False, default=func.now())
    is_working: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="gpu_storages")
    gpu = relationship("Gpu", back_populates="gpu_storages")
    order = relationship("Order", back_populates="gpu_storages")
