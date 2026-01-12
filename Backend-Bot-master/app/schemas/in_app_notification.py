from typing import Optional
from . import BaseSchema
from datetime import datetime, timezone
from pydantic import Field

class InAppNotificationCreate(BaseSchema):
    user_id: int = Field(..., gt=0)
    type: str = Field(..., max_length=255)
    title: str = Field(..., max_length=255)
    message: str = Field(..., max_length=255)
    data: Optional[dict] = Field(None)
    dedup_key: Optional[str] = Field(None)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class InAppNotificationUpdate(BaseSchema):
    type: Optional[str] = Field(None, max_length=255)
    title: Optional[str] = Field(None, max_length=255)
    message: Optional[str] = Field(None, max_length=255)
    data: Optional[dict] = Field(None)
    read_at: Optional[datetime] = Field(None)
    created_at: Optional[datetime] = Field(None)


class InAppNotificationSchema(InAppNotificationCreate):
    id: int = Field(..., gt=0)
    read_at: Optional[datetime] = Field(None)
