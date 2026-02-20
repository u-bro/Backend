from pydantic import Field, model_validator
from datetime import datetime, timezone
from .base import BaseSchema
from .role import RoleSchema


class UserSchemaValidated(BaseSchema):
    first_name: str | None = Field(None, min_length=2, max_length=100, pattern=r"^[A-Za-zА-Яа-яЁё\-\s]+$")
    last_name: str | None = Field(None, min_length=2, max_length=100, pattern=r"^[A-Za-zА-Яа-яЁё\-\s]+$")
    middle_name: str | None = Field(None, min_length=2, max_length=100, pattern=r"^[A-Za-zА-Яа-яЁё\-\s]+$")
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=255, pattern=r"^[A-Za-z0-9._-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}$")
    city: str | None = Field(None, max_length=100)
    photo_url: str | None = Field(None)

    @model_validator(mode="after")
    def check_first_name_and_last_name(self):
        if self.first_name and not self.last_name or self.last_name and not self.first_name:
            raise ValueError('first_name and last_name must be provided together')
        return self


class UserSchemaCreate(UserSchemaValidated):
    role_id: int = Field(..., gt=0)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserSchemaUpdate(UserSchemaCreate):
    last_active: datetime | None = Field(None)
    is_active: bool | None = Field(None)
    role_id: int | None = Field(None, gt=0)
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserSchemaUpdateMe(UserSchemaValidated):
    role_id: int | None = Field(None, gt=0)
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserSchema(UserSchemaUpdate):
    id: int = Field(..., gt=0)


class UserSchemaMe(UserSchema):
    role_name: str
    is_active_ride: bool = False


class UserSchemaWithRole(UserSchema):
    role: RoleSchema