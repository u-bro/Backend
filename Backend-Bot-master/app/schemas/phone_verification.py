from typing import Optional
from datetime import datetime, timezone
from . import BaseSchema
from pydantic import Field


class PhoneVerificationUpdate(BaseSchema):
    user_id: Optional[int] = None
    phone: Optional[str] = None
    code: Optional[str] = None
    expires_at: Optional[datetime] = None
    status: Optional[str] = None
    attempts: Optional[int] = None
    is_registred: Optional[bool] = None


class PhoneVerificationSchemaCreate(BaseSchema):
    user_id: int = Field(...)
    phone: str = Field(..., max_length=20)
    code: str = Field(..., max_length=10)
    expires_at: datetime | None = Field(None)
    status: Optional[str] = None
    attempts: Optional[int] = 0
    is_registred: Optional[bool] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PhoneVerificationVerifyRequest(BaseSchema):
    code: str = Field(..., max_length=10)
    phone: str | None = Field(None, max_length=20)


class PhoneVerificationSchema(PhoneVerificationSchemaCreate):
    id: int
