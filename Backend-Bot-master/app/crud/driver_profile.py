from app.crud.base import CrudBase
from app.models.driver_profile import DriverProfile
from app.schemas.driver_profile import DriverProfileSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update


class DriverProfileCrud(CrudBase[DriverProfile, DriverProfileSchema]):
    def __init__(self) -> None:
        super().__init__(DriverProfile, DriverProfileSchema)

    async def ride_count_increment(self, session: AsyncSession, id: int):
        stmt = update(self.model).where(self.model.id == id).values(ride_count=self.model.ride_count + 1).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None


driver_profile_crud = DriverProfileCrud()
