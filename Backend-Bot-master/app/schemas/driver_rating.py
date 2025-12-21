from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class DriverRatingCreateIn(BaseModel):
    driver_profile_id: int
    ride_id: int
    rate: int
    comment: Optional[str] = None
    created_at: Optional[datetime] = None


class DriverRatingCreate(DriverRatingCreateIn):
    client_id: int


class DriverRatingUpdate(BaseModel):
    rate: Optional[int] = None
    comment: Optional[str] = None
    created_at: Optional[datetime] = None


class DriverRatingSchema(DriverRatingCreate):
    id: int
