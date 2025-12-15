from pydantic import Field
from datetime import datetime
from . import BaseSchema


class TransactionSchemaCreate(BaseSchema):
    user_id: int = Field(..., gt=0)
    is_withdraw: bool = Field(True)
    amount: float = Field(..., gt=0)


class TransactionSchema(TransactionSchemaCreate):
    id: int = Field(..., gt=0)
    created_at: datetime = Field(None)
