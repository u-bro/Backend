from pydantic import Field
from datetime import datetime, timezone
from .base import BaseSchema


class UserSchemaCreate(BaseSchema):
    first_name: str | None = Field(None, min_length=2, max_length=100)
    last_name: str | None = Field(None, min_length=2, max_length=100)
    middle_name: str | None = Field(None, min_length=2, max_length=100)
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    photo_url: str | None = Field(None)
    role_id: int = Field(..., gt=0)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserSchemaUpdate(UserSchemaCreate):
    last_active: datetime | None = Field(None)
    is_active: bool | None = Field(None) 
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserSchemaUpdateMe(BaseSchema):
    first_name: str | None = Field(None, min_length=2, max_length=100)
    last_name: str | None = Field(None, min_length=2, max_length=100)
    middle_name: str | None = Field(None, min_length=2, max_length=100)
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    photo_url: str | None = Field(None)
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserSchema(UserSchemaUpdate):
    id: int = Field(..., gt=0)


class UserSchemaMe(UserSchema):
    role_name: str
    is_active_ride: bool = False
