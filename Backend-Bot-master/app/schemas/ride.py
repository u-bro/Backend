from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from .base import BaseSchema

class RideSchemaIn(BaseSchema):
    status: str | None = Field('requested', max_length=50)
    status_reason: str | None = Field(None, max_length=255)
    pickup_address: str | None = Field(None, max_length=500)
    pickup_lat: float | None = Field(None)
    pickup_lng: float | None = Field(None)
    dropoff_address: str | None = Field(None, max_length=500)
    dropoff_lat: float | None = Field(None)
    dropoff_lng: float | None = Field(None)
    scheduled_at: datetime | None = Field(None)
    distance_meters: int | None = Field(None, ge=0)
    duration_seconds: int | None = Field(None, ge=0)
    commission_id: int | None = Field(None)
    tariff_plan_id: int = Field(..., gt=0)


class RideSchemaCreate(RideSchemaIn):
    client_id: int = Field(..., gt=0)

class RideSchema(RideSchemaCreate):
    id: int = Field(..., gt=0)
    started_at: datetime | None = Field(None)
    completed_at: datetime | None = Field(None)
    canceled_at: datetime | None = Field(None)
    expected_fare: float | None = Field(None, ge=0)
    expected_fare_snapshot: dict | None = Field(None)
    ride_metadata: dict | None = Field(None)
    created_at: datetime | None = Field(None)
    updated_at: datetime | None = Field(None)
