from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from . import BaseSchema
from pydantic import Field

class PhoneVerificationCreate(BaseModel):
    user_id: int
    phone: str
    code: str
    expires_at: Optional[datetime] = None
    status: Optional[str] = None
    attempts: Optional[int] = 0


class PhoneVerificationUpdate(BaseModel):
    user_id: Optional[int] = None
    phone: Optional[str] = None
    code: Optional[str] = None
    expires_at: Optional[datetime] = None
    status: Optional[str] = None
    attempts: Optional[int] = None


class PhoneVerificationSchema(BaseModel):
    id: int
    user_id: int
    phone: str
    code: str
    expires_at: Optional[datetime] = None
    status: Optional[str] = None
    attempts: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PhoneVerificationSchemaCreate(BaseSchema):
    user_id: int = Field(...)
    phone: str = Field(..., max_length=20)
    code: str = Field(..., max_length=10)
    expires_at: datetime | None = Field(None)

class PhoneVerificationVerifyRequest(BaseSchema):
    code: str = Field(..., max_length=10)
