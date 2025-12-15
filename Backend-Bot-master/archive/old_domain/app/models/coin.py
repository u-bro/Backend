from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DECIMAL
from app.db import Base, metadata


class Coin(Base):
    __tablename__ = "coins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    coin_type_multiplier: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)
    algorithm_type_multiplier: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)

    algorithm_type: Mapped[str] = mapped_column(String(50), nullable=False)

