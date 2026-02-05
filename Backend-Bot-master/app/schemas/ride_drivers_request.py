from typing import Literal
from .base import BaseSchema
from datetime import datetime, timezone
from pydantic import Field
from .driver_profile import DriverProfileSchema
from .car import CarSchema


class RideDriversRequestCreate(BaseSchema):
    ride_id: int = Field(..., gt=0)
    driver_profile_id: int = Field(..., gt=0)
    car_id: int | None = Field(None, gt=0)
    status: Literal['requested'] | None = Field("requested", max_length=50)
    eta: str | None = Field(None, max_length=50)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class RideDriversRequestUpdate(BaseSchema):
    status: Literal['accepted', 'rejected', 'canceled'] = Field(..., max_length=50)
    eta: str | None = Field(None, max_length=50)
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class RideDriversRequestSchema(RideDriversRequestCreate):
    id: int = Field(..., gt=0)
    status: Literal['requested', 'accepted', 'rejected', 'canceled'] = Field(..., max_length=50)
    updated_at: datetime | None = None


class RideDriversRequestSchemaDetailed(RideDriversRequestSchema):
    driver_profile: DriverProfileSchema = Field(...)
    car: CarSchema | None = Field(None)

