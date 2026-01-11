from typing import Optional
from .base import BaseSchema
from datetime import datetime, timezone
from pydantic import Field


class DriverProfileCreate(BaseSchema):
    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    birth_date: Optional[datetime] = None
    photo_url: Optional[str] = None
    license_number: Optional[str] = None
    license_category: Optional[str] = None
    license_issued_at: Optional[datetime] = None
    license_expires_at: Optional[datetime] = None
    experience_years: Optional[int] = None
    qualification_level: Optional[str] = None
    classes_allowed: list[str] = []
    documents_status: Optional[str] = None
    documents_review_notes: Optional[str] = None
    current_class: Optional[str] = None
    ride_count: int = 0
    rating_avg: int = 0
    rating_count: int = 0
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class DriverProfileUpdateMe(BaseSchema):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    birth_date: Optional[datetime] = None
    photo_url: Optional[str] = None
    license_number: Optional[str] = None
    license_category: Optional[str] = None
    experience_years: Optional[int] = None
    current_class: Optional[str] = None
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class DriverProfileUpdate(DriverProfileCreate):
    user_id: Optional[int] = None
    ride_count: Optional[int] = None
    rating_avg: Optional[int] = None
    rating_count: Optional[int] = None
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))
    classes_allowed: Optional[list[str]] = None


class DriverProfileApproveIn(BaseSchema):
    approved: bool = True
    approved_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))


class DriverProfileApprove(DriverProfileApproveIn):
    approved_by: int


class DriverProfileSchema(DriverProfileUpdate):
    id: int
    approved: bool = False
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
