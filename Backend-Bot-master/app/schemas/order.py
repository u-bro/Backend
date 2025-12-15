from pydantic import Field
from datetime import datetime
from . import BaseSchema


class OrderSchemaUpdate(BaseSchema):
    price: float | None = Field(None, ge=0)


class OrderSchemaCreate(BaseSchema):
    user_gpu_storage_id: int | None = Field(None, ge=0)
    price: float | None = Field(None, ge=0)


class OrderSchema(OrderSchemaCreate):
    id: int
    created_at: datetime | None = Field(None)
