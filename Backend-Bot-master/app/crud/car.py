from app.crud.base import CrudBase
from app.models import Car
from app.schemas.car import CarSchema, CarCreate
from app.schemas.driver_profile import DriverProfileUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from .driver_profile import driver_profile_crud

class CarCrud(CrudBase[Car, CarSchema]):
    def __init__(self) -> None:
        super().__init__(Car, CarSchema)

    async def get_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int, **kwargs) -> list[CarSchema]:
        existing = await session.execute(select(self.model).where(self.model.driver_profile_id == driver_profile_id))
        items = existing.scalars().all()
        return [self.schema.model_validate(item) for item in items] 

    async def create(self, session: AsyncSession, create_obj: CarCreate) -> CarSchema | None:
        stmt = insert(self.model).values(create_obj.model_dump()).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        if not result:
            return None
        await driver_profile_crud.update(session, create_obj.driver_profile_id, DriverProfileUpdate(current_car_id=result.id))
        return self.schema.model_validate(result) if result else None

car_crud = CarCrud()
