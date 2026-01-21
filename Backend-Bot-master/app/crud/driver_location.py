from fastapi import HTTPException
from app.crud.base import CrudBase
from app.models.driver_location import DriverLocation
from app.schemas.driver_location import DriverLocationSchema, DriverLocationUpdate, DriverLocationUpdateMe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from app.models import RideDriversRequest

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
        return await self.update(session, item.id, update_obj)

    async def update_me(self, session: AsyncSession, driver_profile_id: int, update_obj: DriverLocationUpdate | DriverLocationUpdateMe, **kwargs) -> DriverLocationSchema:
        item = await self.get_by_driver_profile_id(session, driver_profile_id)
        if not item:
            raise HTTPException(status_code=404, detail="Driver location not found")
        if item.status != 'offline' and item.status != 'online' and item.status != 'waiting_ride' and update_obj.status:
            raise HTTPException(status_code=400, detail="Driver is busy, status can't be changed")
        return await self.update(session, item.id, update_obj)

    async def update(self, session: AsyncSession, id: int, update_obj: DriverLocationUpdate | DriverLocationUpdateMe) -> DriverLocationSchema | None:
        update_data = update_obj.model_dump(exclude_none=True)
        existing = await self.get_by_id(session, id)
        if not update_data:
            return existing
        
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(update_data)
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        result_validated = self.schema.model_validate(result) if result else None
        if existing.status == 'waiting_ride' and (update_obj.status == 'offline' or update_obj.status == 'online'):
            await self.cancel_requests_by_driver_profile_id(session, result_validated.driver_profile_id)
        return result_validated

    async def cancel_requests_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int):
        await session.execute(update(RideDriversRequest).where(and_(RideDriversRequest.driver_profile_id == driver_profile_id, RideDriversRequest.status == 'requested')).values({"status": "canceled"}))


driver_location_crud = DriverLocationCrud()
