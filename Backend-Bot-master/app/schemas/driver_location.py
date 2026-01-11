from typing import Optional, Literal
from .base import BaseSchema
from datetime import datetime, timezone
from pydantic import Field


class DriverLocationCreate(BaseSchema):
    driver_profile_id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy_m: Optional[int] = None
    provider: Optional[str] = None
    status: Literal["offline", "online", "busy"] = "offline"
    last_seen_at: Optional[datetime] = None
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class DriverLocationUpdate(BaseSchema):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy_m: Optional[int] = None
    provider: Optional[str] = None
    status: Optional[Literal["offline", "online", "busy"]] = None
    last_seen_at: Optional[datetime] = None


class DriverLocationUpdateMe(DriverLocationUpdate):
    status: Optional[Literal["offline", "online"]] = None


class DriverLocationSchema(DriverLocationCreate):
    id: int
