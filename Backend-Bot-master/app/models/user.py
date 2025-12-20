from sqlalchemy import Integer, String, TIMESTAMP, Boolean, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base, metadata


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    created_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP, nullable=True, default=func.now())
    last_active_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP, nullable=True, default=func.now())

    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), nullable=True)

    role = relationship("Role")
    transactions = relationship("Transaction", back_populates="user")
