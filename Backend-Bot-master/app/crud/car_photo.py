from app.crud.base import CrudBase
from app.models import CarPhoto
from app.schemas.car_photo import CarPhotoSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException


class CarPhotoCrud(CrudBase[CarPhoto, CarPhotoSchema]):
    def __init__(self) -> None:
        super().__init__(CarPhoto, CarPhotoSchema)

    async def get_by_car_id(self, session: AsyncSession, car_id: int, **kwargs) -> list[CarPhotoSchema]:
        existing = await session.execute(select(self.model).where(self.model.car_id == car_id))
        items = existing.scalars().all()
        return [self.schema.model_validate(item) for item in items] 

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
