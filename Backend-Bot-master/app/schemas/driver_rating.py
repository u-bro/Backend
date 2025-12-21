from typing import Optional
from . import BaseSchema
from datetime import datetime
from pydantic import Field

class DriverRatingCreateIn(BaseSchema):
    driver_profile_id: int = Field(..., gt=0)
    ride_id: int = Field(..., gt=0)
    rate: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=255)
    created_at: Optional[datetime] = Field(None)


class DriverRatingCreate(DriverRatingCreateIn):
    client_id: int = Field(..., gt=0)


class DriverRatingUpdate(BaseSchema):
    rate: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=255)
    created_at: Optional[datetime] = Field(None)


class DriverRatingSchema(DriverRatingCreate):
    id: int = Field(..., gt=0)


class DriverRatingAvgOut(BaseSchema):
    avg: float = Field(..., ge=0)