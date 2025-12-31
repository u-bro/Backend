from typing import Optional
from . import BaseSchema
from datetime import datetime


class TransactionCreate(BaseSchema):
    user_id: int
    is_withdraw: bool
    amount: float


class TransactionUpdate(BaseSchema):
    user_id: Optional[int] = None
    is_withdraw: Optional[bool] = None
    amount: Optional[float] = None


class TransactionSchema(BaseSchema):
    id: int
    user_id: int
    is_withdraw: bool
    amount: float
    created_at: datetime | None = None

    class Config:
        from_attributes = True
