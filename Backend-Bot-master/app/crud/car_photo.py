from app.crud.base import CrudBase
from app.models import Car, CarPhoto, DriverDocument, DriverProfile
from app.schemas.car_photo import CarPhotoSchema
from app.crud.document import document_crud
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException


class CarPhotoCrud(CrudBase[CarPhoto, CarPhotoSchema]):
    def __init__(self) -> None:
        super().__init__(CarPhoto, CarPhotoSchema)

    async def get_by_car_id(self, session: AsyncSession, car_id: int, **kwargs) -> list[CarPhotoSchema]:
        existing = await session.execute(select(self.model).where(self.model.car_id == car_id))
        items = existing.scalars().all()
        if items:
            return [self.schema.model_validate(item) for item in items]

        # Registration stores car control photos as CAR_PHOTO_* driver documents.
        # They belong to the driver's current car even though the legacy table is empty.
        profile_id = await session.scalar(
            select(DriverProfile.id)
            .join(Car, Car.driver_profile_id == DriverProfile.id)
            .where(Car.id == car_id, DriverProfile.current_car_id == car_id)
        )
        if profile_id is None:
            return []

        documents = (
            await session.execute(
                select(DriverDocument)
                .where(
                    DriverDocument.driver_profile_id == profile_id,
                    DriverDocument.doc_type.startswith("CAR_PHOTO_"),
                    DriverDocument.file_bucket_key.is_not(None),
                )
                .order_by(DriverDocument.doc_type)
            )
        ).scalars().all()

        return [
            CarPhotoSchema(
                id=document.id,
                car_id=car_id,
                type=document.doc_type.removeprefix("CAR_PHOTO_"),
                description=None,
                status=document.status,
                photo_url=document_crud.presigned_get_url(document.file_bucket_key),
                created_at=document.created_at,
            )
            for document in documents
        ]

    async def update(self, session: AsyncSession, id: int, update_obj: CarPhotoSchema) -> CarPhotoSchema | None:
        update_data = update_obj.model_dump(exclude_none=True)
        existing = await session.get(self.model, id)
        if not existing:
            raise HTTPException(status_code=404, detail="Car photo not found")

        if not update_data:
            return self.schema.model_validate(existing)
        
        if existing.status == 'created':
            update_obj.status = 'sent'

        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(update_data)
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None


car_photo_crud = CarPhotoCrud()
