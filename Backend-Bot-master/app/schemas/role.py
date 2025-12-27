from .base import BaseSchema
from datetime import datetime
from pydantic import Field


class RoleCreate(BaseSchema):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=255)


class RoleUpdate(BaseSchema):
    code: str | None = Field(None, max_length=50)
    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=255)


class RoleSchema(RoleCreate):
    id: int = Field(..., gt=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None
