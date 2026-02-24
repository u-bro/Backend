from typing import Optional
from .base import BaseSchema
from datetime import datetime, timezone
from pydantic import Field


class CommissionBase(BaseSchema):
    name: Optional[str] = None
    percentage: Optional[float] = None
    fixed_amount: Optional[float] = None
    currency: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class CommissionCreate(CommissionBase):
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class CommissionUpdate(CommissionBase):
    pass


class CommissionSchema(CommissionBase):
    id: int
    created_at: datetime | None = None
