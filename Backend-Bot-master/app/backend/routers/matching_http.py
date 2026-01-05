from typing import Any, Dict
from fastapi import HTTPException, Query, Request
from app.backend.routers.base import BaseRouter
from app.crud.driver_profile import driver_profile_crud
from app.crud.ride import ride_crud
from app.services.driver_tracker import driver_tracker
from app.services.matching_engine import RideRequest, matching_engine
from app.services.websocket_manager import manager
from app.schemas.matching import AcceptRideRequest, AcceptRideResponse, RideFeedItem, DriverRegistration, FindDriversRequest


class MatchingHttpRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(matching_engine, "/matching")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/driver/register", self.register_driver, methods=["POST"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/feed/{{driver_profile_id}}", self.get_ride_feed, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/accept/{{ride_id}}", self.accept_ride, methods=["POST"], status_code=200, response_model=AcceptRideResponse)
        self.router.add_api_route(f"{self.prefix}/find-drivers", self.find_drivers_for_ride, methods=["POST"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/stats", self.get_matching_stats, methods=["GET"], status_code=200)

    async def register_driver(self, request: Request, data: DriverRegistration) -> Dict[str, Any]:
        profile = await driver_profile_crud.get_by_id(request.state.session, data.driver_profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Driver profile not found")

        state = driver_tracker.register_driver(
            driver_profile_id=data.driver_profile_id,
            user_id=data.user_id,
            classes_allowed=data.classes_allowed,
            rating=data.rating,
        )

        return {
            "status": "registered",
            "driver_profile_id": state.driver_profile_id,
            "classes_allowed": list(state.classes_allowed),
        }

    async def get_ride_feed(self, request: Request, driver_profile_id: int, limit: int = Query(20, ge=1, le=100)) -> Dict[str, Any]:
        driver = driver_tracker.get_driver(driver_profile_id)
        if not driver:
            raise HTTPException(
                status_code=400,
                detail="Driver not registered in tracker. Call POST /matching/driver/register first",
            )

        if driver.latitude is None:
            raise HTTPException(
                status_code=400,
                detail="Driver location not set. Send location_update via WebSocket",
            )

        pending_rides = await ride_crud.get_requested_rides(request.state.session, limit=limit * 2)
        rides_dict = [
            {
                "id": r.id,
                "client_id": r.client_id,
                "status": r.status,
                "pickup_address": r.pickup_address,
                "pickup_lat": r.pickup_lat,
                "pickup_lng": r.pickup_lng,
                "dropoff_address": r.dropoff_address,
                "dropoff_lat": r.dropoff_lat,
                "dropoff_lng": r.dropoff_lng,
                "expected_fare": r.expected_fare,
                "ride_class": "economy",  # TODO: добавить поле в модель
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in pending_rides
            if r.pickup_lat and r.pickup_lng
        ]
        feed = matching_engine.get_driver_feed(driver_profile_id, rides_dict, limit)

        return {
            "driver_profile_id": driver_profile_id,
            "driver_status": driver.status.value,
            "count": len(feed),
            "rides": feed,
        }

    async def accept_ride(self, request: Request, ride_id: int, data: AcceptRideRequest) -> AcceptRideResponse:
        ride, status = await ride_crud.accept_ride_idempotent(
            session=request.state.session,
            ride_id=ride_id,
            driver_profile_id=data.driver_profile_id,
            actor_id=data.user_id,
        )

        success = status in ("accepted", "already_yours")

        messages = {
            "accepted": "Заказ успешно принят!",
            "already_yours": "Этот заказ уже был принят вами",
            "already_taken": "Заказ уже принят другим водителем",
            "not_found": "Заказ не найден",
            "invalid_status": "Заказ недоступен для принятия",
        }

        if success:
            driver_tracker.assign_ride(data.driver_profile_id, ride_id)
            if ride:
                await manager.send_personal_message(
                    ride.client_id,
                    {
                        "type": "ride_accepted",
                        "ride_id": ride_id,
                        "driver_profile_id": data.driver_profile_id,
                        "message": "Водитель принял ваш заказ!",
                    },
                )

            await request.state.session.commit()

        return AcceptRideResponse(
            success=success,
            status=status,
            ride_id=ride_id,
            message=messages.get(status, "Unknown status"),
        )

    async def find_drivers_for_ride(self, request: Request, data: FindDriversRequest, limit: int = Query(10, ge=1, le=50)) -> Dict[str, Any]:
        ride_request = RideRequest(
            ride_id=data.ride_id,
            client_id=0,
            ride_class=data.ride_class,
            pickup_lat=data.pickup_lat,
            pickup_lng=data.pickup_lng,
            dropoff_lat=data.dropoff_lat,
            dropoff_lng=data.dropoff_lng,
            search_radius_km=data.search_radius_km,
        )

        drivers = matching_engine.find_drivers(ride_request, limit=limit)

        return {
            "ride_id": data.ride_id,
            "ride_class": data.ride_class,
            "search_radius_km": data.search_radius_km,
            "found": len(drivers),
            "drivers": [d.to_dict() for d in drivers],
        }

    async def get_matching_stats(self) -> Dict[str, Any]:
        return matching_engine.get_stats()


matching_http_router = MatchingHttpRouter().router
