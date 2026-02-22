from typing import Literal
from pydantic import Field, model_validator
from datetime import datetime, timezone
from .base import BaseSchema
from .driver_rating import DriverRatingSchema
from .driver_profile import DriverProfileSchema


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
    distance_str: str | None = Field(None, max_length=50)
    duration_seconds: int | None = Field(None, ge=0)
    duration_str: str | None = Field(None, max_length=50)
    commission_id: int = Field(..., gt=0)
    tariff_plan_id: int = Field(..., gt=0)
    ride_class: Literal["light", "pro", "vip", "elite"] = Field(..., max_length=50)
    ride_type: Literal["with_car", "without_car"] = Field("with_car", max_length=50)
    comment: str | None = Field(None, max_length=500)


class RideSchemaCreate(RideSchemaIn):
    client_id: int = Field(..., gt=0)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def check_route(self):
        if self.pickup_lat == self.dropoff_lat and self.pickup_lng == self.dropoff_lng:
            raise ValueError('Incorrect route: pickup and dropoff coordinates are equal')
        if self.pickup_address == self.dropoff_address:
            raise ValueError('Incorrect route: pickup and dropoff addresses are equal')
        return self


class RideSchema(RideSchemaCreate):
    id: int = Field(..., gt=0)
    status: Literal["requested", "canceled", "waiting_commission", "accepted", "on_the_way", "arrived", "started", "completed"] = Field("requested", max_length=50)
    driver_profile_id: int | None = Field(None, gt=0)
    started_at: datetime | None = Field(None)
    completed_at: datetime | None = Field(None)
    canceled_at: datetime | None = Field(None)
    expected_fare: float | None = Field(None, ge=0)
    expected_fare_snapshot: dict | None = Field(None)
    commission_amount: float | None = Field(None, ge=0)
    actual_fare: float | None = Field(None, ge=0)
    ride_metadata: dict | None = Field(None)
    updated_at: datetime | None = Field(None)
    is_anomaly: bool | None = Field(False)
    anomaly_reason: str | None = Field(None, max_length=255)


class RideSchemaWithCanceledValidator(BaseSchema):
    @model_validator(mode="after")
    def check_canceled_at(self):
        if self.status != "canceled" and self.canceled_at is not None:
            raise ValueError('canceled_at should be None if status is not \"canceled\"')
        return self

    @model_validator(mode="after")
    def set_canceled_at(self):
        if self.status == "canceled" and self.canceled_at is None:
            self.canceled_at = datetime.now(timezone.utc)
        return self


class RideSchemaUpdateByClient(RideSchemaWithCanceledValidator):
    status: Literal["canceled"] | None = Field(None, max_length=50)
    status_reason: str | None = Field(None, max_length=255)
    pickup_address: str | None = Field(None, max_length=500)
    pickup_lat: float | None = Field(None)
    pickup_lng: float | None = Field(None)
    dropoff_address: str | None = Field(None, max_length=500)
    dropoff_lat: float | None = Field(None)
    dropoff_lng: float | None = Field(None)
    distance_meters: int | None = Field(None, ge=0)
    distance_str: str | None = Field(None, max_length=50)
    duration_seconds: int | None = Field(None, ge=0)
    duration_str: str | None = Field(None, max_length=50)
    comment: str | None = Field(None, max_length=500)
    canceled_at: datetime | None = Field(None)
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class RideschemaUpdateAfterCommission(BaseSchema):
    status: Literal["accepted"] = Field("accepted", max_length=50)
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class RideSchemaUpdateByDriver(RideSchemaWithCanceledValidator):
    status: Literal["on_the_way", "arrived", "started", "canceled"] | None = Field(None, max_length=50)
    status_reason: str | None = Field(None, max_length=255)
    started_at: datetime | None = Field(None)
    canceled_at: datetime | None = Field(None)
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def check_started_at(self):
        if self.status != "started" and self.started_at is not None:
            raise ValueError('started_at should be None if status is not \"started\"')
        return self

    @model_validator(mode="after")
    def set_started_at_when_started(self):
        if self.status == "started" and self.started_at is None:
            self.started_at = datetime.now(timezone.utc)
        return self


class RideSchemaAcceptByDriver(BaseSchema):
    status: Literal["waiting_commission"] = Field("waiting_commission", max_length=50)
    driver_profile_id: int | None = Field(None, gt=0)
    status_reason: str | None = Field(None, max_length=255)
    eta: dict | None = Field(None)
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class RideSchemaFinishByDriver(BaseSchema):
    status: Literal["completed"] = Field("completed", max_length=50)
    completed_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))
    actual_fare: float = Field(0, ge=0)
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class RideSchemaFinishWithAnomaly(RideSchemaFinishByDriver):
    is_anomaly: bool | None = Field(False)
    anomaly_reason: str | None = Field(None, max_length=255)
    ride_metadata: dict | None = Field(None)


class RideSchemaHistory(BaseSchema):
    id: int = Field(..., gt=0)
    status: Literal["requested", "canceled", "waiting_commission", "accepted", "on_the_way", "arrived", "started", "completed"] = Field("requested", max_length=50)
    pickup_address: str | None = Field(None, max_length=500)
    dropoff_address: str | None = Field(None, max_length=500)
    expected_fare: float | None = Field(None, ge=0)
    commission_amount: float | None = Field(None, ge=0)
    actual_fare: float | None = Field(None, ge=0)
    ride_class: Literal["light", "pro", "vip", "elite"] = Field(..., max_length=50)
    created_at: datetime | None = Field(None)


class RideSchemaWithRating(RideSchema):
    driver_rating: DriverRatingSchema | None = None

class RideSchemaWithDriverProfile(RideSchema):
    driver_profile: DriverProfileSchema | None = None