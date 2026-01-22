from app.crud.base import CrudBase
from app.models import RideDriversRequest
from app.schemas.ride_drivers_request import RideDriversRequestSchema, RideDriversRequestUpdate, RideDriversRequestCreate, RideDriversRequestSchemaDetailed
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select, update, insert, and_
from sqlalchemy.orm import selectinload
from .in_app_notification import in_app_notification_crud
from .driver_profile import driver_profile_crud
from .ride import ride_crud
from .driver_tracker import driver_tracker, DriverStatus
from app.services.websocket_manager import manager_driver_feed
from app.schemas.in_app_notification import InAppNotificationCreate
from app.services import fcm_service
from app.schemas.push import PushNotificationData
from app.schemas.ride import RideSchemaAcceptByDriver
from fastapi import HTTPException


class RideDriversRequestCrud(CrudBase[RideDriversRequest, RideDriversRequestSchema]):
    def __init__(self) -> None:
        super().__init__(RideDriversRequest, RideDriversRequestSchema)

    async def get_by_ride_id(self, session: AsyncSession, ride_id: int):
        result = await session.execute(select(self.model).where(self.model.ride_id == ride_id))
        ride_drivers_requests = result.scalars().all()
        return [self.schema.model_validate(ride_drivers_request) for ride_drivers_request in ride_drivers_requests]

    async def get_by_ride_id_detailed(self, session: AsyncSession, ride_id: int):
        result = await session.execute(select(self.model).options(selectinload(self.model.driver_profile)).options(selectinload(self.model.car)).where(self.model.ride_id == ride_id))
        ride_drivers_requests = result.scalars().all()
        return [RideDriversRequestSchemaDetailed.model_validate(ride_drivers_request) for ride_drivers_request in ride_drivers_requests]

    async def get_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int):
        result = await session.execute(select(self.model).where(self.model.driver_profile_id == driver_profile_id))
        ride_drivers_requests = result.scalars().all()
        return [self.schema.model_validate(ride_drivers_request) for ride_drivers_request in ride_drivers_requests]

    async def get_requested_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int):
        result = await session.execute(select(self.model).where(and_(self.model.driver_profile_id == driver_profile_id, self.model.status == "requested")))
        ride_drivers_requests = result.scalars().all()
        return [self.schema.model_validate(ride_drivers_request) for ride_drivers_request in ride_drivers_requests]

    async def get_requested_by_ride_id_and_driver_profile_id(self, session: AsyncSession, ride_id: int, driver_profile_id: int):
        result = await session.execute(select(self.model).where(and_(self.model.ride_id == ride_id, self.model.driver_profile_id == driver_profile_id, self.model.status == "requested")))
        ride_drivers_request = result.scalar_one_or_none()
        return self.schema.model_validate(ride_drivers_request) if ride_drivers_request else None

    async def create(self, session: AsyncSession, create_obj: RideDriversRequestCreate) -> RideDriversRequestSchema | None:
        existing_ride_drivers_requests = await self.get_requested_by_driver_profile_id(session, create_obj.driver_profile_id)
        if existing_ride_drivers_requests and len(existing_ride_drivers_requests) > 0:
            raise HTTPException(status_code=400, detail="Ride request for this driver already exists")

        stmt = insert(self.model).values(create_obj.model_dump()).returning(self.model)
        result = await self.execute_get_one(session, stmt)
        if not result:
            return None
        
        ride = await ride_crud.get_by_id(session, result.ride_id)
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        
        result_validated = self.schema.model_validate(result)
        await driver_tracker.set_status_by_driver(session, result.driver_profile_id, DriverStatus.WAITING_RIDE)

        await in_app_notification_crud.create(session, InAppNotificationCreate(user_id=ride.client_id, type="ride_offer", title="New ride offer", message="New ride offer from driver", data={"offer_id": result.id, "ride_id": result.ride_id, "driver_profile_id": result.driver_profile_id}, dedup_key=str(result.id)))
        await fcm_service.send_to_user(session, ride.client_id, PushNotificationData(title="New ride offer", body="New ride offer from driver"))
        return result_validated

    async def update(self, session: AsyncSession, id: int, update_obj: RideDriversRequestUpdate) -> RideDriversRequestSchema | None:
        update_data = update_obj.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(session, id)
        
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(update_data)
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        if not result:
            return None
        
        result_validated = self.schema.model_validate(result)
        driver_profile = await driver_profile_crud.get_by_id(session, result.driver_profile_id)

        if result.status == 'accepted':
            accepted = await ride_crud.accept(session, result.ride_id, RideSchemaAcceptByDriver(driver_profile_id=result.driver_profile_id), driver_profile.user_id)
            if not accepted:
                raise HTTPException(status_code=400, detail="Ride request is not accepted. Perhaps, ride is already accepted")
            await driver_tracker.assign_ride(session, driver_profile.id, accepted.id)

            await manager_driver_feed.send_personal_message(driver_profile.user_id, {"type": "ride_offer_accepted", "message": "Your ride offer is accepted", "data": result_validated.model_dump(mode='json')})

            other_requests = await self.get_by_ride_id(session, result.ride_id)
            for request in other_requests:
                if request.id != id and request.status == 'requested':
                    await self.update(session, request.id, RideDriversRequestUpdate(status='rejected'))
        if result.status == 'rejected':
            await driver_tracker.set_status_by_driver(session, result.driver_profile_id, DriverStatus.ONLINE)

            await manager_driver_feed.send_personal_message(driver_profile.user_id, {"type": "ride_offer_rejected", "message": "Ride offer rejected", "data": result_validated.model_dump(mode='json')})
        if result.status == 'canceled':
            await driver_tracker.set_status_by_driver(session, result.driver_profile_id, DriverStatus.ONLINE)
        return result_validated
            
    async def reject_by_ride_id(self, session: AsyncSession, ride_id: int):
        result = await session.execute(select(self.model).where(self.model.ride_id == ride_id))
        ride_drivers_requests = result.scalars().all()
        
        ids = [ride_drivers_request.id for ride_drivers_request in ride_drivers_requests]

        await session.execute(update(self.model).where(self.model.id.in_(ids)).values({"status": "rejected"}))
        for request in ride_drivers_requests:
            await driver_tracker.set_status_by_driver(session, request.driver_profile_id, DriverStatus.ONLINE)
            await manager_driver_feed.send_personal_message(request.driver_profile_id, {"type": "ride_offer_rejected", "message": "Ride offer rejected", "data": self.schema.model_validate(request).model_dump(mode='json')})

    async def cancel_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int):
        await session.execute(update(self.model).where(and_(self.model.driver_profile_id == driver_profile_id, self.model.status == 'requested')).values({"status": "canceled"}))

ride_drivers_request_crud = RideDriversRequestCrud()
