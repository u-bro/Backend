from datetime import datetime, timezone
from pydantic import Field
from .base import BaseSchema


class DriverModerationInfoSchema(BaseSchema):
    id: int = Field(..., gt=0)
    code: str = Field(..., max_length=50)
    message: str = Field(..., max_length=255)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))
