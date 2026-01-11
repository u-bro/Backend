from .base import BaseSchema
from datetime import datetime, timezone
from pydantic import Field


class RoleCreate(BaseSchema):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=255)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class RoleUpdate(BaseSchema):
    code: str | None = Field(None, max_length=50)
    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=255)
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class RoleSchema(RoleCreate):
    id: int = Field(..., gt=0)
    updated_at: datetime | None = None
