from typing import Any, List
from fastapi import Request, Depends, HTTPException
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.routers.base import BaseRouter
from app.crud.ride import ride_crud
from app.models import Ride
from app.schemas.ride import RideSchema, RideSchemaIn, RideSchemaCreate, RideSchemaUpdateByClient, RideSchemaUpdateByDriver, RideSchemaFinishWithAnomaly, RideSchemaFinishByDriver, RideSchemaAcceptByDriver
from app.schemas.push import PushNotificationData
from app.schemas.in_app_notification import InAppNotificationCreate
from app.schemas.ride_drivers_request import RideDriversRequestCreate, RideDriversRequestSchema, RideDriversRequestUpdate
from app.backend.deps import require_role, get_current_user_id, get_current_driver_profile_id, require_owner, require_driver_profile
from app.models import Ride
from app.crud import document_crud, in_app_notification_crud, driver_profile_crud, user_crud, ride_drivers_request_crud, car_crud
from app.services.chat_service import chat_service
from app.services import pdf_generator, fcm_service, manager_driver_feed
from app.crud.driver_tracker import driver_tracker


class RideRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(ride_crud, "/rides")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/me/client", self.get_my_as_client, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/me/driver", self.get_my_as_driver, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role(["admin"]))])
        
        self.router.add_api_route(f"{self.prefix}/{{id}}/client", self.update_by_client, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"])), Depends(require_owner(Ride, 'client_id'))])
        self.router.add_api_route(f"{self.prefix}/{{id}}/driver", self.update_by_driver, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["driver", "admin"])), Depends(require_driver_profile(Ride))])
        self.router.add_api_route(f"{self.prefix}/{{id}}/accept", self.accept_ride, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}/cancel-request", self.cancel_ride_request, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}/finish", self.finish_ride_by_driver, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["driver", "admin"]))])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[RideSchema]:
        items = await super().get_paginated(request, page, page_size)
        return TypeAdapter(List[RideSchema]).validate_python(items)

    async def get_by_id(self, request: Request, id: int) -> RideSchema:
        return await super().get_by_id(request, id)

    async def get_my_as_client(self, request: Request, user_id: int = Depends(get_current_user_id)):
        return await self.model_crud.get_by_client_id(request.state.session, user_id)
    
    async def get_my_as_driver(self, request: Request, driver_profile_id: int = Depends(get_current_driver_profile_id)):
        return await self.model_crud.get_by_driver_profile_id(request.state.session, driver_profile_id)

    async def create(self, request: Request, create_obj: RideSchemaIn, user_id: int = Depends(get_current_user_id)) -> RideSchema:
        create_obj = RideSchemaCreate(client_id=user_id, **create_obj.model_dump())
        ride = await super().create(request, create_obj)
        return ride

    async def update(self, request: Request, id: int, update_obj: RideSchema, user_id: int = Depends(get_current_user_id)) -> RideSchema:
        return await self.model_crud.update(request.state.session, id, update_obj, user_id)

    async def delete(self, request: Request, id: int) -> RideSchema:
        return await super().delete(request, id)

    async def update_by_client(self, request: Request, id: int, update_obj: RideSchemaUpdateByClient, user_id: int = Depends(get_current_user_id)) -> RideSchema:
        session = request.state.session
        old_ride = await self.model_crud.get_by_id(session, id)
        if not old_ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        ride = await self.model_crud.update(session, id, update_obj, user_id)

        driver_profile = await driver_profile_crud.get_by_id(session, ride.driver_profile_id)
        if driver_profile:
            await manager_driver_feed.send_personal_message(driver_profile.user_id, {"type": "ride_changed", "message": "Ride is changed by client", "data": ride.model_dump(mode="json")})

        if update_obj.status == 'canceled':
            await ride_drivers_request_crud.reject_by_ride_id(session, id)
            await chat_service.save_message_and_send_to_ride(session=session, ride_id=ride.id, text="Ride is canceled by client", message_type="system")
            await self.send_notifications(session, ride.client_id, "ride_canceled", f"Ride status is canceled by you", "Check ride info, client", ride.model_dump(mode="json"), f"{ride.id}_{old_ride.status}_{ride.status}")
            await driver_tracker.release_ride(session, ride.driver_profile_id)
        return ride

    async def accept_ride(self, request: Request, id: int, update_obj: RideSchemaAcceptByDriver, driver_profile_id: int = Depends(get_current_driver_profile_id), user_id: int = Depends(get_current_user_id)) -> RideDriversRequestSchema:
        session = request.state.session
        driver_profile = await driver_profile_crud.get_by_id(session, driver_profile_id)
        if not driver_profile:
            raise HTTPException(status_code=404, detail="Driver profile not found")
        request = await ride_drivers_request_crud.create(session, RideDriversRequestCreate(ride_id=id, driver_profile_id=driver_profile_id, car_id=driver_profile.current_car_id, eta=update_obj.eta,status="requested"))
        ride = await ride_crud.get_by_id(session, id)
        await manager_driver_feed.send_personal_message(user_id, {"type": "ride_request_sent", "data": ride.model_dump(mode="json")})
        await self.send_notifications(session, ride.client_id, "ride_request_accepted", "Ride request accepted", "Now yoe need to pay commission", ride.model_dump(mode="json"), ride.id)
        return request

    async def cancel_ride_request(self, request: Request, id: int, driver_profile_id: int = Depends(get_current_driver_profile_id)) -> RideDriversRequestSchema:
        session = request.state.session
        existing = await ride_drivers_request_crud.get_requested_by_ride_id_and_driver_profile_id(session, id, driver_profile_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Ride request not found")
        request = await ride_drivers_request_crud.update(session, existing.id, RideDriversRequestUpdate(status="canceled"))
        return request

    async def update_by_driver(self, request: Request, id: int, update_obj: RideSchemaUpdateByDriver, user_id: int = Depends(get_current_user_id)) -> RideSchema:
        session = request.state.session
        old_ride = await self.model_crud.get_by_id(session, id)
        if not old_ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        ride = await self.model_crud.update(session, id, update_obj, user_id)
        await self.send_notifications(session, ride.client_id, "ride_status_changed", f"Ride status is changed from \"{old_ride.status}\" to \"{ride.status}\" by driver", "Check ride info, client", ride.model_dump(mode="json"), f"{ride.id}_{old_ride.status}_{ride.status}")
        await manager_driver_feed.send_personal_message(user_id, {"type": "ride_changed", "message": "Ride is changed by you", "data": ride.model_dump(mode="json")})

        if update_obj.status == 'canceled':
            await chat_service.save_message_and_send_to_ride(session=session, ride_id=ride.id, text="Ride is canceled by driver", message_type="system")
            await driver_tracker.release_ride(session, ride.driver_profile_id)
        return ride

    async def finish_ride_by_driver(self, request: Request, id: int, update_obj: RideSchemaFinishByDriver, ride: Ride = Depends(require_driver_profile(Ride)), user_id: int = Depends(get_current_user_id), generate_check: bool = False) -> RideSchema:
        session = request.state.session
        update_obj = RideSchemaFinishWithAnomaly(is_anomaly=str(ride.expected_fare) != str(update_obj.actual_fare), **update_obj.model_dump())
        ride = await self.model_crud.update(session, id, update_obj, user_id)
        await manager_driver_feed.send_personal_message(user_id, {"type": "ride_finished", "message": "Ride is finished", "data": ride.model_dump(mode="json")})
        await self.send_notifications(session, ride.client_id, "ride_finished", "Ride is finished", "Don't forget to rate the ride", ride.model_dump(mode="json"), ride.id)
        await driver_tracker.release_ride(session, ride.driver_profile_id)

        if generate_check:
            key = f"receipts/rides/{id}/receipt.pdf"
            client = await user_crud.get_by_id(session, ride.client_id)
            driver_profile = await driver_profile_crud.get_by_id(session, ride.driver_profile_id)
            client_full_name = [word for word in [client.first_name, client.last_name, client.middle_name] if word]
            driver_full_name = [word for word in [driver_profile.first_name, driver_profile.last_name, driver_profile.middle_name] if word]
            pdf_check = await pdf_generator.generate_ride_receipt(id, " ".join(client_full_name), " ".join(driver_full_name), ride.pickup_address, ride.dropoff_address, update_obj.actual_fare, ride.distance_meters / 1000, ride.duration_seconds / 60)
            await document_crud.upload_pdf_bytes(key, pdf_check)
        
        return ride

    async def send_notifications(self, session: AsyncSession, client_id: int, type: str, title: str, message: str, data: dict, dedup_key: Any):
        await in_app_notification_crud.create(session, InAppNotificationCreate(user_id=client_id, type=type, title=title, message=message, data=data, dedup_key=str(dedup_key) if dedup_key else None))
        await fcm_service.send_to_user(session, client_id, PushNotificationData(title=title, body=message))
    

ride_router = RideRouter().router
