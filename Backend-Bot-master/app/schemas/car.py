from .base import BaseSchema
from datetime import datetime, timezone
from pydantic import Field


class CarCreate(BaseSchema):
    driver_profile_id: int = Field(..., gt=0)
    model: str = Field(..., max_length=100)
    number: str = Field(..., max_length=100)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class CarUpdate(BaseSchema):
    model: str | None = Field(None, max_length=100)
    number: str | None = Field(None, max_length=100)
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class CarSchema(CarCreate):
    id: int = Field(..., gt=0)
    updated_at: datetime | None = None
