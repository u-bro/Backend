from sqlalchemy import Integer, String, TIMESTAMP, func, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class Commission(Base):
    __tablename__ = 'commissions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    percentage: Mapped[float | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    fixed_amount: Mapped[float | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    valid_from = mapped_column(TIMESTAMP, nullable=True)
    valid_to = mapped_column(TIMESTAMP, nullable=True)
    created_at = mapped_column(TIMESTAMP, nullable=True, default=func.now())
