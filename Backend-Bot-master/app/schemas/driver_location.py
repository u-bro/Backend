from typing import Optional, Literal
from .base import BaseSchema
from datetime import datetime


class DriverLocationCreate(BaseSchema):
    driver_profile_id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy_m: Optional[int] = None
    provider: Optional[str] = None
    status: Literal["offline", "online", "busy"] = "offline"
    last_seen_at: Optional[datetime] = None


class DriverLocationUpdate(BaseSchema):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy_m: Optional[int] = None
    provider: Optional[str] = None
    status: Optional[Literal["offline", "online", "busy"]] = None
    last_seen_at: Optional[datetime] = None



class DriverLocationSchema(BaseSchema):
    id: int
    driver_profile_id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy_m: Optional[int] = None
    provider: Optional[str] = None
    status: Literal["offline", "online", "busy"] = "offline"
    last_seen_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
