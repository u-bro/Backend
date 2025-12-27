from typing import Optional
from .base import BaseSchema
from datetime import datetime


class RoleCreate(BaseSchema):
    code: str
    name: Optional[str] = None
    description: Optional[str] = None


class RoleUpdate(BaseSchema):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


class RoleSchema(BaseSchema):
    id: int
    code: str
    name: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
