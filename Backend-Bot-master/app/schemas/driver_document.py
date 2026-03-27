from typing import Optional, Literal
from .base import BaseSchema
from pydantic import model_validator
from datetime import datetime
from app.enum import DriverDocumentType


class DriverDocumentCreate(BaseSchema):
    driver_profile_id: int
    doc_type: str
    file_bucket_key: str | None = None
    status: Optional[Literal['created']] = 'created'

    @model_validator(mode="after")
    def check_doc_type(self):
        if self.doc_type not in DriverDocumentType:
            raise ValueError('Incorrect doc type')
 
        return self


class DriverDocumentDriverUpdate(BaseSchema):
    doc_type: Optional[str] = None
    file_bucket_key: Optional[str] = None
    status: Optional[Literal['updated']] = None

class DriverDocumentAdminUpdateIn(BaseSchema):
    status: Optional[Literal['approved', 'rejected']] = None

class DriverDocumentAdminUpdate(DriverDocumentAdminUpdateIn):
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None


class DriverDocumentSchema(DriverDocumentCreate):
    id: int
    status: Optional[Literal['created', 'updated', 'approved', 'rejected']] = None
    created_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None

class DriverDocumentSchemaWithURL(BaseSchema):
    id: int | None
    car_photo_id: int | None
    driver_profile_id: int
    doc_type: str
    file_url: str | None
    status: Optional[Literal['created', 'updated', 'approved', 'rejected']] = None
    created_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None  

    @model_validator(mode="after")
    def check_doc_type(self):
        if self.doc_type not in DriverDocumentType:
            raise ValueError('Incorrect doc type')
 
        return self
