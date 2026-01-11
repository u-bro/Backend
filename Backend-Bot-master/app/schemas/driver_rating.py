from typing import Optional
from . import BaseSchema
from datetime import datetime, timezone
from pydantic import Field

class DriverRatingCreateIn(BaseSchema):
    driver_profile_id: int = Field(..., gt=0)
    ride_id: int = Field(..., gt=0)
    rate: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=255)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))

class DriverRatingCreate(DriverRatingCreateIn):
    client_id: int = Field(..., gt=0)


class DriverRatingUpdate(BaseSchema):
    rate: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=255)


class DriverRatingSchema(DriverRatingCreate):
    id: int = Field(..., gt=0)


class DriverRatingAvgOut(BaseSchema):
    avg: float = Field(..., ge=0)