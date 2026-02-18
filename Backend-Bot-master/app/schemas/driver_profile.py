from typing import Optional
from .base import BaseSchema
from datetime import datetime, timezone
from pydantic import Field
from .car import CarSchema


class DriverProfileCreate(BaseSchema):
    user_id: int
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    middle_name: Optional[str] = Field(None, min_length=2, max_length=100)
    birth_date: Optional[datetime] = None
    photo_url: Optional[str] = None
    license_number: Optional[str] = Field(None, max_length=100)
    license_category: Optional[str] = Field(None, max_length=20)
    license_issued_at: Optional[datetime] = None
    license_expires_at: Optional[datetime] = None
    experience_years: Optional[int] = None
    qualification_level: Optional[str] = Field(None, max_length=50)
    classes_allowed: list[str] = []
    documents_status: Optional[str] = Field(None, max_length=50)
    documents_review_notes: Optional[str] = None
    current_class: Optional[str] = None
    current_car_id: Optional[int] = None
    ride_count: int = 0
    rating_avg: float = 0.0
    rating_count: int = 0
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class DriverProfileUpdateMe(BaseSchema):
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    middle_name: Optional[str] = Field(None, min_length=2, max_length=100)
    birth_date: Optional[datetime] = None
    photo_url: Optional[str] = None
    license_number: Optional[str] = Field(None, max_length=100)
    license_category: Optional[str] = Field(None, max_length=20)
    experience_years: Optional[int] = None
    current_class: Optional[str] = None
    current_car_id: Optional[int] = None
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class DriverProfileUpdate(BaseSchema):
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    middle_name: Optional[str] = Field(None, min_length=2, max_length=100)
    birth_date: Optional[datetime] = None
    photo_url: Optional[str] = None
    license_number: Optional[str] = Field(None, max_length=100)
    license_category: Optional[str] = Field(None, max_length=20)
    license_issued_at: Optional[datetime] = None
    license_expires_at: Optional[datetime] = None
    experience_years: Optional[int] = None
    qualification_level: Optional[str] = Field(None, max_length=50)
    classes_allowed: list[str] = []
    documents_status: Optional[str] = Field(None, max_length=50)
    documents_review_notes: Optional[str] = None
    current_class: Optional[str] = None
    current_car_id: Optional[int] = None
    ride_count: Optional[int] = None
    rating_avg: Optional[float] = None
    rating_count: Optional[int] = None
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))
    classes_allowed: Optional[list[str]] = None


class DriverProfileApproveIn(BaseSchema):
    approved: bool = True
    approved_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class DriverProfileApprove(DriverProfileApproveIn):
    approved_by: int


class DriverProfileSchema(DriverProfileCreate):
    id: int
    approved: bool = False
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DriverProfileWithCars(DriverProfileSchema):
    cars: list[CarSchema]