from typing import Optional
from . import BaseSchema
from datetime import datetime, timezone
from pydantic import Field

class DeviceTokenCreate(BaseSchema):
    user_id: int = Field(..., gt=0)
    token: str = Field(..., max_length=255)
    platform: str = Field(..., max_length=255)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class DeviceTokenUpdate(BaseSchema):
    token: Optional[str] = Field(None, max_length=255)
    platform: Optional[str] = Field(None, max_length=255)
    created_at: Optional[datetime] = Field(None)


class DeviceTokenSchema(DeviceTokenCreate):
    id: int = Field(..., gt=0)
