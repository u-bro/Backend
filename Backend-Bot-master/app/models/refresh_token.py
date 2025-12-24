from sqlalchemy import Integer, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP, nullable=True, default=func.now())
    revoked_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP, nullable=True, default=func.now())
    created_at: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP, nullable=True, default=func.now())
