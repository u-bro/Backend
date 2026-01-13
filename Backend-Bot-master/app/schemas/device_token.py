from typing import Literal, Optional
from datetime import datetime, timezone
from pydantic import Field
from .base import BaseSchema

class DeviceTokenIn(BaseSchema):
    token: str = Field(..., max_length=255)
    platform: Literal['android', 'ios'] = Field(...)


class DeviceTokenCreate(DeviceTokenIn):
    user_id: int = Field(..., gt=0)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class DeviceTokenUpdate(BaseSchema):
    token: Optional[str] = Field(None, max_length=255)
    platform: Optional[Literal['android', 'ios']] = Field(None)
    created_at: Optional[datetime] = Field(None)


class DeviceTokenSchema(DeviceTokenCreate):
    id: int = Field(..., gt=0)
