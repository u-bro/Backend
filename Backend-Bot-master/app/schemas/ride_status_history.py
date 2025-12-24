from typing import Optional, Literal
from pydantic import Field
from datetime import datetime
from .base import BaseSchema


class RideStatusHistoryCreate(BaseSchema):
    ride_id: int = Field(..., gt=0)
    from_status: Literal["requested", "canceled", "accepted", "arrived", "started", "completed"] | None = Field(None, max_length=50)
    to_status: Literal["requested", "canceled", "accepted", "arrived", "started", "completed"] = Field(..., max_length=50)
    changed_by: int = Field(..., gt=0)
    actor_role: Literal["client", "driver"] | None = Field(None, max_length=50)
    reason: str | None = Field(None, max_length=255)
    meta: dict | None = Field(None)
    created_at: Optional[datetime] = datetime.utcnow()


class RideStatusHistorySchema(RideStatusHistoryCreate):
    id: int
