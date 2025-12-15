from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DECIMAL, Boolean
from app.db import Base, metadata


class Gpu(Base):
    __tablename__ = "gpus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    income: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    rarity: Mapped[int] = mapped_column(Integer, nullable=False)
    gpu_lvl: Mapped[int] = mapped_column(Integer, nullable=False)
    algorithm_type: Mapped[str] = mapped_column(String(50), nullable=False)
    coin_type: Mapped[str] = mapped_column(String(5), nullable=False)
    is_crafted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)

    gpu_storages = relationship("UserGpuStorage", back_populates="gpu_storages")

