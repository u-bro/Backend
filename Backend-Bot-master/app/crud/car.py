from app.crud.base import CrudBase
from app.models import Car
from app.schemas.car import CarSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class CarCrud(CrudBase[Car, CarSchema]):
    def __init__(self) -> None:
        super().__init__(Car, CarSchema)

    async def get_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int, **kwargs) -> list[CarSchema]:
        existing = await session.execute(select(self.model).where(self.model.driver_profile_id == driver_profile_id))
        items = existing.scalars().all()
        return [self.schema.model_validate(item) for item in items] 

car_crud = CarCrud()
