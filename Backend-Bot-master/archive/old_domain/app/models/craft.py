from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, DECIMAL
from app.db import Base, metadata


# TODO удалить 
class Craft(Base):
    __tablename__ = "craft"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    required_rarity: Mapped[int] = mapped_column(Integer, nullable=False)  # Редкость видеокарт, необходимых для крафта
    base_chance: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)  # Базовый шанс крафта
    chance_modifier: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)  # Модификатор шанса

    min_result_rarity: Mapped[int] = mapped_column(Integer, nullable=False)  # Минимальная редкость результата, если крафт не удался
    max_result_rarity: Mapped[int] = mapped_column(Integer, nullable=False)  # Максимальная редкость результата, если крафт не удался

    crafted_gpu_rarity: Mapped[int] = mapped_column(Integer, nullable=False)  # Редкость крафтовой видеокарты
    fail_penalty_modifier: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False, default=1.0)  # Штраф при провале
    max_craft_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5)  # Лимит крафтовых попыток
