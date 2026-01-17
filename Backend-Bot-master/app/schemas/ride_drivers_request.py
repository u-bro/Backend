from typing import Literal
from .base import BaseSchema
from datetime import datetime, timezone
from pydantic import Field
from .driver_profile import DriverProfileSchema


class RideDriversRequestCreate(BaseSchema):
    ride_id: int = Field(..., gt=0)
    driver_profile_id: int = Field(..., gt=0)
    status: Literal['requested'] = Field(..., max_length=50)
    eta: str | None = Field(None, max_length=50)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class RideDriversRequestUpdate(BaseSchema):
    status: Literal['accepted', 'rejected'] = Field(..., max_length=50)
    eta: str | None = Field(None, max_length=50)
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class RideDriversRequestSchema(RideDriversRequestCreate):
    id: int = Field(..., gt=0)
    status: Literal['requested', 'accepted', 'rejected'] = Field(..., max_length=50)
    updated_at: datetime | None = None


class RideDriversRequestSchemaWithDriverProfile(RideDriversRequestSchema):
    driver_profile: DriverProfileSchema = Field(...)

