from fastapi import HTTPException
from app.crud.base import CrudBase
from app.models.driver_location import DriverLocation
from app.schemas.driver_location import DriverLocationSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select

class DriverLocationCrud(CrudBase[DriverLocation, DriverLocationSchema]):
    def __init__(self) -> None:
        super().__init__(DriverLocation, DriverLocationSchema)

    async def get_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int, **kwargs) -> DriverLocationSchema:
        existing = await session.execute(select(self.model).where(self.model.driver_profile_id == driver_profile_id))
        item = existing.scalar_one_or_none()
        return self.schema.model_validate(item) if item else None

    async def update_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int, update_obj, **kwargs) -> DriverLocationSchema:
        item = self.get_by_driver_profile_id(session, driver_profile_id)
        if not item:
            raise HTTPException(status_code=404, detail="Driver profile not found")

        return await super().update(session, existing.id, update_obj)

driver_location_crud = DriverLocationCrud()
