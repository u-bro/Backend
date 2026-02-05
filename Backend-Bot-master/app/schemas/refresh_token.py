from pydantic import Field
from . import BaseSchema
from datetime import datetime


class RefreshTokenIn(BaseSchema):
    user_id: int = Field(...)


class RefreshTokenCreate(RefreshTokenIn):
    user_id: int = Field(...)
    token: str = Field(...)
    expires_at: datetime = Field(...)
    revoked_at: datetime | None = Field(default=None)
    created_at: datetime = Field(...)


class RefreshTokenSchema(RefreshTokenCreate):
    id: int = Field(...)
