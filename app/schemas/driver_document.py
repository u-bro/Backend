from typing import Optional
from .base import BaseSchema
from datetime import datetime


class DriverDocumentCreate(BaseSchema):
    driver_profile_id: int
    doc_type: str
    file_url: str
    status: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None


class DriverDocumentUpdate(BaseSchema):
    driver_profile_id: Optional[int] = None
    doc_type: Optional[str] = None
    file_url: Optional[str] = None
    status: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None


class DriverDocumentSchema(BaseSchema):
    id: int
    driver_profile_id: int
    doc_type: str
    file_url: str
    status: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
