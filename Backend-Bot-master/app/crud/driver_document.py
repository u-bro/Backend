from app.crud.base import CrudBase
from app.models.driver_document import DriverDocument
from app.schemas.driver_document import DriverDocumentSchema, DriverDocumentSchemaWithURL, DriverDocumentCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, insert, update
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
            file_url = document_crud.presigned_get_url(item.file_bucket_key) if item.file_bucket_key else None
            documents.append(DriverDocumentSchemaWithURL(**item_validated.model_dump(), file_url=file_url, car_photo_id=None))

        driver_profile = await driver_profile_crud.get_by_id_with_cars(session, driver_profile_id)
        if len(driver_profile.cars):
            car = driver_profile.cars[0]
            car_photos = await car_photo_crud.get_by_car_id(session, car.id)
            for car_photo in car_photos:
                documents.append(DriverDocumentSchemaWithURL(id=None, car_photo_id=car_photo.id, driver_profile_id=driver_profile_id, doc_type=f"CAR_PHOTO_{car_photo.type}", file_url=car_photo.photo_url, created_at=car_photo.created_at, status=car_photo.status))

        return [DriverDocumentSchemaWithURL.model_validate(document) for document in documents]

    async def get_by_driver_profile_id_and_doc_type(self, session: AsyncSession, driver_profile_id: int, doc_type: str, **kwargs):
        result = await session.execute(select(self.model).where(and_(self.model.driver_profile_id == driver_profile_id, self.model.doc_type == doc_type)))
        item = result.scalar_one_or_none()
        return self.schema.model_validate(item) if item else None

    async def upsert(self, session: AsyncSession, upsert_obj: DriverDocumentCreate, **kwargs) -> DriverDocumentSchema:
        existing = await self.get_by_driver_profile_id_and_doc_type(session, upsert_obj.driver_profile_id, upsert_obj.doc_type)

        if existing:
            update_data = upsert_obj.model_dump(exclude_none=True)
            if not update_data:
                return existing
            
            update_data['status'] = 'updated'
            stmt = (
                update(self.model)
                .where(self.model.id == existing.id)
                .values(update_data)
                .returning(self.model)
            )
            result = await self.execute_get_one(session, stmt)
            return self.schema.model_validate(result) if result else None

        stmt = insert(self.model).values(upsert_obj.model_dump()).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

driver_document_crud = DriverDocumentCrud()
