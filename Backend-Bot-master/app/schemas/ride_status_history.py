from typing import Literal
from pydantic import Field
from datetime import datetime, timezone
from .base import BaseSchema
from app.enum import RoleCode


class RideStatusHistoryCreate(BaseSchema):
    ride_id: int = Field(..., gt=0)
    from_status: Literal["requested", "canceled", "waiting_commission", "accepted", "on_the_way", "arrived", "started", "completed"] | None = Field(None, max_length=50)
    to_status: Literal["requested", "canceled", "waiting_commission", "accepted", "on_the_way", "arrived", "started", "completed"] = Field(..., max_length=50)
    changed_by: int = Field(..., gt=0)
    actor_role: Literal[RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN] | None = Field(None, max_length=50)
    reason: str | None = Field(None, max_length=255)
    meta: dict | None = Field(None)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class RideStatusHistorySchema(RideStatusHistoryCreate):
    id: int
