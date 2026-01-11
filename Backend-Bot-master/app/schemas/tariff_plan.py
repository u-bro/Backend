from pydantic import Field
from datetime import datetime, timezone
from .base import BaseSchema


class TariffPlanCreate(BaseSchema):
    name: str | None = Field(None, max_length=100)
    base_fare: float = Field(..., gt=0)
    rate_per_meter: float = Field(..., gt=0)
    multiplier: float = Field(..., gt=0)
    effective_from: datetime = Field(None)
    effective_to: datetime | None = Field(None)
    rules: dict | None = Field(None)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class TariffPlanUpdate(BaseSchema):
    name: str | None = Field(None, max_length=100)
    base_fare: float | None = Field(None, gt=0)
    rate_per_meter: float | None = Field(None, gt=0)
    multiplier: float | None = Field(None, gt=0)
    effective_from: datetime | None = Field(None)
    effective_to: datetime | None = Field(None)
    rules: dict | None = Field(None)
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class TariffPlanSchema(TariffPlanCreate):
    id: int = Field(..., gt=0)
    updated_at: datetime | None = Field(None)
