from fastapi import HTTPException
from app.crud.base import CrudBase
from app.models.driver_location import DriverLocation
from app.schemas.driver_location import DriverLocationSchema, DriverLocationUpdate, DriverLocationUpdateMe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class DriverLocationCrud(CrudBase[DriverLocation, DriverLocationSchema]):
    def __init__(self) -> None:
        super().__init__(DriverLocation, DriverLocationSchema)

    async def get_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int, **kwargs) -> DriverLocationSchema:
        existing = await session.execute(select(self.model).where(self.model.driver_profile_id == driver_profile_id))
        item = existing.scalar_one_or_none()
        return self.schema.model_validate(item) if item else None

    async def update_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int, update_obj: DriverLocationUpdate | DriverLocationUpdateMe, **kwargs) -> DriverLocationSchema:
        item = await self.get_by_driver_profile_id(session, driver_profile_id)
        if not item:
            raise HTTPException(status_code=404, detail="Driver location not found")
        return await super().update(session, item.id, update_obj)

    async def update_me(self, session: AsyncSession, driver_profile_id: int, update_obj: DriverLocationUpdate | DriverLocationUpdateMe, **kwargs) -> DriverLocationSchema:
        item = await self.get_by_driver_profile_id(session, driver_profile_id)
        if not item:
            raise HTTPException(status_code=404, detail="Driver location not found")
        if item.status == 'busy' and update_obj.status:
            raise HTTPException(status_code=400, detail="Driver is busy, status can't be changed")
        return await super().update(session, item.id, update_obj)

driver_location_crud = DriverLocationCrud()
