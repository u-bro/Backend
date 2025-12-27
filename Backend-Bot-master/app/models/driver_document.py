from sqlalchemy import Integer, String, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class DriverDocument(Base):
    __tablename__ = 'driver_documents'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    driver_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey('driver_profiles.id'), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_url: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    reviewed_at = mapped_column(TIMESTAMP, nullable=True)
    created_at = mapped_column(TIMESTAMP, nullable=True, default=func.now())

    driver_profile = relationship('DriverProfile')
