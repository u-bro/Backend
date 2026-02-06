from app.crud.base import CrudBase
from app.models import CarPhoto
from app.schemas.car_photo import CarPhotoSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class CarPhotoCrud(CrudBase[CarPhoto, CarPhotoSchema]):
    def __init__(self) -> None:
        super().__init__(CarPhoto, CarPhotoSchema)

    async def get_by_car_id(self, session: AsyncSession, car_id: int, **kwargs) -> list[CarPhotoSchema]:
        existing = await session.execute(select(self.model).where(self.model.car_id == car_id))
        items = existing.scalars().all()
        return [self.schema.model_validate(item) for item in items] 

car_photo_crud = CarPhotoCrud()
