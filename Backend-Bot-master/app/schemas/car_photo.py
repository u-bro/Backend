from .base import BaseSchema
from datetime import datetime, timezone
from pydantic import Field
from typing import Literal


class CarPhotoCreate(BaseSchema):
    car_id: int = Field(..., gt=0)
    type: str = Field(..., max_length=50)
    description: str | None = Field(None, max_length=255)
    status: Literal['created'] | None = 'created'
    photo_url: str | None = Field(None)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class CarPhotoUpdate(BaseSchema):
    type: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=255)
    status: Literal['updated'] | None = 'updated'
    photo_url: str | None = Field(None)
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class CarPhotoSchema(CarPhotoCreate):
    id: int = Field(..., gt=0)
    status: Literal['created', 'updated', 'approved', 'rejected'] | None = None
    updated_at: datetime | None = None
