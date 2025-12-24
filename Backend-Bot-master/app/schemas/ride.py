from typing import Literal
from pydantic import Field
from datetime import datetime
from .base import BaseSchema

class RideSchemaIn(BaseSchema):
    status: Literal["requested"] = Field("requested", max_length=50)
    status_reason: str | None = Field(None, max_length=255)
    pickup_address: str = Field(None, max_length=500)
    pickup_lat: float = Field(...)
    pickup_lng: float = Field(...)
    dropoff_address: str = Field(None, max_length=500)
    dropoff_lat: float = Field(...)
    dropoff_lng: float = Field(...)
    scheduled_at: datetime | None = Field(None)
    distance_meters: int = Field(..., ge=0)
    duration_seconds: int | None = Field(None, ge=0)
    commission_id: int | None = Field(None)
    tariff_plan_id: int = Field(..., gt=0)


class RideSchemaCreate(RideSchemaIn):
    client_id: int = Field(..., gt=0)

class RideSchema(RideSchemaCreate):
    id: int = Field(..., gt=0)
    status: Literal["requested", "canceled", "accepted", "arrived", "started", "completed"] = Field("requested", max_length=50)
    driver_profile_id: int | None = Field(None, gt=0)
    started_at: datetime | None = Field(None)
    completed_at: datetime | None = Field(None)
    canceled_at: datetime | None = Field(None)
    expected_fare: float | None = Field(None, ge=0)
    expected_fare_snapshot: dict | None = Field(None)
    actual_fare: float | None = Field(None, ge=0)
    ride_metadata: dict | None = Field(None)
    created_at: datetime | None = Field(None)
    updated_at: datetime | None = Field(None)
    is_anomaly: bool | None = Field(False)
    anomaly_reason: str | None = Field(None, max_length=255)


class RideSchemaUpdateByClient(BaseSchema):
    status: Literal["requested", "canceled"] | None = Field(None, max_length=50)
    status_reason: str | None = Field(None, max_length=255)
    pickup_address: str | None = Field(None, max_length=500)
    pickup_lat: float | None = Field(None)
    pickup_lng: float | None = Field(None)
    dropoff_address: str | None = Field(None, max_length=500)
    dropoff_lat: float | None = Field(None)
    dropoff_lng: float | None = Field(None)
    distance_meters: int | None = Field(None, ge=0)
    canceled_at: datetime | None = Field(None)


class RideSchemaUpdateByDriver(BaseSchema):
    status: Literal["accepted", "arrived", "started", "canceled"] | None = Field(None, max_length=50)
    status_reason: str | None = Field(None, max_length=255)
    started_at: datetime | None = Field(None)


class RideSchemaAcceptByDriver(BaseSchema):
    status: Literal["accepted"] = Field("accepted", max_length=50)
    driver_profile_id: int | None = Field(None, gt=0)
    status_reason: str | None = Field(None, max_length=255)
    started_at: datetime | None = Field(None)


class RideSchemaFinishByDriver(BaseSchema):
    status: Literal["completed"] = Field("completed", max_length=50)
    completed_at: datetime | None = Field(None)
    actual_fare: float = Field(0, ge=0)


class RideSchemaFinishWithAnomaly(RideSchemaFinishByDriver):
    is_anomaly: bool | None = Field(False)
    anomaly_reason: str | None = Field(None, max_length=255)
