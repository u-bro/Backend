from typing import Optional
from .base import BaseSchema
from datetime import datetime, timezone
from pydantic import Field

class CommissionCreate(BaseSchema):
    name: Optional[str] = None
    percentage: Optional[float] = None
    fixed_amount: Optional[float] = None
    currency: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class CommissionUpdate(BaseSchema):
    name: Optional[str] = None
    percentage: Optional[float] = None
    fixed_amount: Optional[float] = None
    currency: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class CommissionSchema(BaseSchema):
    id: int
    name: Optional[str] = None
    percentage: Optional[float] = None
    fixed_amount: Optional[float] = None
    currency: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
