from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class DriverRatingCreate(BaseModel):
    driver_profile_id: int
    ride_id: int
    rate: int
    comment: Optional[str] = None
    created_at: Optional[datetime] = None


class DriverRatingUpdate(DriverRatingCreate):
    driver_profile_id: Optional[int] = None
    ride_id: Optional[int] = None
    rate: Optional[int] = None
    comment: Optional[str] = None
    created_at: Optional[datetime] = None


class DriverRatingSchema(DriverRatingCreate):
    id: int
