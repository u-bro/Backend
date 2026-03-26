from app.crud.base import CrudBase
from app.models.driver_document import DriverDocument
from app.schemas.driver_document import DriverDocumentSchema, DriverDocumentSchemaWithURL
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .car_photo import car_photo_crud
from .car import driver_profile_crud
from .document import document_crud


class DriverDocumentCrud(CrudBase[DriverDocument, DriverDocumentSchema]):
    def __init__(self) -> None:
        super().__init__(DriverDocument, DriverDocumentSchema)

    async def get_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int, **kwargs) -> list[DriverDocumentSchemaWithURL]:
        existing = await session.execute(select(self.model).where(self.model.driver_profile_id == driver_profile_id))
        items = existing.scalars().all()
        documents = []

        for item in items:
            item_validated = DriverDocumentSchema.model_validate(item)
            file_url = await document_crud.presigned_get_url(item.file_bucket_key) if item.file_bucket_key else None
            documents.append(DriverDocumentSchemaWithURL(**item_validated.model_dump(), file_url=file_url))

        driver_profile = await driver_profile_crud.get_by_id_with_cars(session, driver_profile_id)
        if len(driver_profile.cars):
            car = driver_profile.cars[0]
            car_photos = await car_photo_crud.get_by_car_id(session, car.id)
            for car_photo in car_photos:
                documents.append(DriverDocumentSchemaWithURL(id=None, car_photo_id=car_photo.id, driver_profile_id=driver_profile_id, doc_type=f"CAR_PHOTO_{car_photo.type}", file_url=car_photo.photo_url, created_at=car_photo.created_at, status=car_photo.status))

        return [DriverDocumentSchemaWithURL.model_validate(document) for document in documents]


driver_document_crud = DriverDocumentCrud()
