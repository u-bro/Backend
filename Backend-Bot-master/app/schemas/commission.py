from typing import Optional
from .base import BaseSchema
from datetime import datetime


class CommissionCreate(BaseSchema):
    name: Optional[str] = None
    percentage: Optional[float] = None
    fixed_amount: Optional[float] = None
    currency: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class CommissionUpdate(CommissionCreate):
    pass


class CommissionSchema(BaseSchema):
    id: int
    name: Optional[str] = None
    percentage: Optional[float] = None
    fixed_amount: Optional[float] = None
    currency: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
