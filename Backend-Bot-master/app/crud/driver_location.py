from fastapi import HTTPException
from app.crud.base import CrudBase
from app.models.driver_location import DriverLocation
from app.schemas.driver_location import DriverLocationSchema, DriverLocationUpdate, DriverLocationUpdateMe
from app.schemas.in_app_notification import InAppNotificationCreate
from app.schemas.ride_drivers_request import RideDriversRequestSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from app.models import RideDriversRequest, Ride
from .in_app_notification import in_app_notification_crud
from app.enum import DriverStatus
from app.const import ACTIVE_RIDE_STATUSES


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
        
        stmt = (update(self.model).where(self.model.id == id).values(update_data).returning(self.model))
        result = await self.execute_get_one(session, stmt)
        result_validated = self.schema.model_validate(result) if result else None
        if update_obj.status == 'offline':
            await self.cancel_requests_by_driver_profile_id(session, result_validated.driver_profile_id)
        return result_validated

    async def cancel_requests_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int):
        # Local import avoids the CRUD module cycle.
        from .ride_drivers_request import ride_drivers_request_crud

        await ride_drivers_request_crud.cancel_by_driver_profile_id(session, driver_profile_id, "driver_offline")

    async def update_status_with_ride_info_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int) -> DriverLocationSchema | None:
        existing = await self.get_by_driver_profile_id(session, driver_profile_id)
        if not existing:
            return None

        driver_active_rides = await session.execute(select(Ride).where(and_(Ride.driver_profile_id == driver_profile_id, Ride.status.in_(ACTIVE_RIDE_STATUSES))))
        driver_active_rides_result = driver_active_rides.scalars().all()

        driver_active_ride_requests = await session.execute(select(RideDriversRequest).where(and_(RideDriversRequest.driver_profile_id == driver_profile_id, RideDriversRequest.status == "requested")))
        driver_active_ride_requests_result = driver_active_ride_requests.scalars().all()
        current_status = DriverStatus.BUSY if len(driver_active_rides_result) > 0 else DriverStatus.WAITING_RIDE if len(driver_active_ride_requests_result) > 0 else DriverStatus.ONLINE

        if existing.status != current_status:
            return await self.update(session, existing.id, DriverLocationUpdate(status=current_status))

        return existing

driver_location_crud = DriverLocationCrud()
