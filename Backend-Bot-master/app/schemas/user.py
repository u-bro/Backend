from pydantic import Field
from datetime import datetime
from . import BaseSchema


class UserSchemaCreate(BaseSchema):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    middle_name: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    photo_url: str | None = Field(None)


class UserSchema(UserSchemaCreate):
    id: int = Field(..., gt=0)
    created_at: datetime | None = Field(None)
    last_active: datetime | None = Field(None)
    is_active: bool | None = Field(None)


class UserSchemaMe(UserSchema):
    role_name: str
