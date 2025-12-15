from pydantic import Field
from datetime import datetime
from . import BaseSchema


class UserGpuStorageSchemaUpdate(BaseSchema):
    is_working: bool | None = Field(False)


class UserGpuStorageSchemaCreate(BaseSchema):
    user_id: int = Field(..., gt=0)
    gpu_id: int = Field(..., gt=0)
    is_working: bool | None = Field(False)


class UserGpuStorageSchema(UserGpuStorageSchemaCreate):
    id: int = Field(..., gt=0)
    added_at: datetime = Field(None)
