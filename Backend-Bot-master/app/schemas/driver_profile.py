from typing import Optional, Literal
from .base import BaseSchema
from datetime import datetime, timezone
from pydantic import Field, field_validator, model_validator
from .car import CarSchema
from .driver_moderation_info import DriverModerationInfoSchema
from app.enum import RideClass
from app.config import DRIVER_PROFILE_INITIAL_RATING_AVG, DRIVER_PROFILE_INITIAL_RATING_COUNT


RIDE_CLASSES_LITERAL = Literal[RideClass.LIGHT, RideClass.PRO, RideClass.VIP, RideClass.ELITE]

class DriverProfileValidated(BaseSchema):
    first_name: Optional[str] = Field(None, min_length=2, max_length=100, pattern=r"^[A-Za-zА-Яа-яЁё\-\s]+$")
    last_name: Optional[str] = Field(None, min_length=2, max_length=100, pattern=r"^[A-Za-zА-Яа-яЁё\-\s]+$")
    middle_name: Optional[str] = Field(None, max_length=100, pattern=r"^[A-Za-zА-Яа-яЁё\-\s]*$")
    birth_date: Optional[datetime] = None
    photo_url: Optional[str] = None
    license_number: Optional[str] = Field(None, max_length=100)
    license_category: Optional[str] = Field(None, max_length=20)
    experience_years: Optional[int] = Field(None, ge=0)
    current_class: Optional[RIDE_CLASSES_LITERAL] = None
    current_car_id: Optional[int] = None

    @model_validator(mode="after")
    def check_first_name_and_last_name(self):
        if self.first_name and not self.last_name or self.last_name and not self.first_name:
            raise ValueError('first_name and last_name must be provided together')
        return self


class DriverProfileCreate(DriverProfileValidated):
    user_id: int | None = None
    license_issued_at: Optional[datetime] = None
    license_expires_at: Optional[datetime] = None
    classes_allowed: list[RIDE_CLASSES_LITERAL] = []
    ride_count: int = Field(0, ge=0)
    rating_avg: float = Field(DRIVER_PROFILE_INITIAL_RATING_AVG, ge=0)
    rating_count: int = Field(DRIVER_PROFILE_INITIAL_RATING_COUNT, ge=0)
    status: Literal['waiting_register'] | None = Field('waiting_register', max_length=50)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class DriverProfileUpdateMe(DriverProfileValidated):
    classes_allowed: Optional[list[RIDE_CLASSES_LITERAL]] = Field(None, min_length=1)
    status: Literal['waiting_approved'] | None = Field(None, max_length=50)
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("classes_allowed")
    @classmethod
    def classes_allowed_must_be_unique(cls, value):
        if value is not None and len(value) != len(set(value)):
            raise ValueError("classes_allowed must contain unique values")
        return value


class DriverProfileUpdate(DriverProfileValidated):
    license_issued_at: Optional[datetime] = None
    license_expires_at: Optional[datetime] = None
    ride_count: Optional[int] = Field(None, ge=0)
    rating_avg: Optional[float] = Field(None, ge=0)
    rating_count: Optional[int] = Field(None, ge=0)
    status: Literal['waiting_moderation'] | None = Field(None, max_length=50)
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))
    classes_allowed: Optional[list[RIDE_CLASSES_LITERAL]] = Field(None, min_length=1)

    @field_validator("classes_allowed")
    @classmethod
    def classes_allowed_must_be_unique(cls, value):
        if value is not None and len(value) != len(set(value)):
            raise ValueError("classes_allowed must contain unique values")
        return value


class DriverProfileApproveIn(BaseSchema):
    approved: bool = True
    approved_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: Literal['waiting_approved', 'approved'] | None = Field('approved', max_length=50)
    classes_allowed: list[RIDE_CLASSES_LITERAL] = Field(default_factory=lambda: [RideClass.LIGHT], min_length=1)

    @field_validator("classes_allowed")
    @classmethod
    def classes_allowed_must_be_unique(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("classes_allowed must contain unique values")
        return value


class DriverProfileApprove(DriverProfileApproveIn):
    approved_by: int


class DriverProfileSchema(DriverProfileCreate):
    id: int
    approved: bool = False
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    status: Literal['waiting_register', 'waiting_approved', 'waiting_moderation', 'approved', 'rejected'] | None = Field(None, max_length=50)
    updated_at: Optional[datetime] = None


class DriverProfileWithCars(DriverProfileSchema):
    cars: list[CarSchema]
    moderation_info: list[DriverModerationInfoSchema]


class DriverModerationAction(BaseSchema):
    status: Literal['approved', 'rejected']
    moderation_info_ids: list[int] = Field(default_factory=list)
    admin_user_id: int = Field(..., gt=0)
    expected_updated_at: datetime
    classes_allowed: Optional[list[RIDE_CLASSES_LITERAL]] = Field(None, min_length=1)

    @field_validator("classes_allowed")
    @classmethod
    def classes_allowed_must_be_unique(cls, value):
        if value is not None and len(value) != len(set(value)):
            raise ValueError("classes_allowed must contain unique values")
        return value
