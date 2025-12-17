from pydantic import Field
from datetime import datetime

from . import BaseSchema


class UserSchemaCreate(BaseSchema):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    username: str | None = Field(None, max_length=100)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=20)
    password_hash: str | None = Field(None, max_length=255)


class UserSchema(UserSchemaCreate):
    id: int = Field(..., gt=0)
    created_at: datetime | None = Field(None)
    last_active: datetime | None = Field(None)
    phone: str | None = Field(None, max_length=20)
    is_active: bool | None = Field(None)

