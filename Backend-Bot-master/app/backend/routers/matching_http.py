from typing import Any, Dict
from fastapi import HTTPException, Query, Request, Depends
from app.backend.routers.base import BaseRouter
from app.crud.driver_profile import driver_profile_crud
from app.crud.ride import ride_crud
from app.services.driver_tracker import DriverState, driver_tracker, DriverStatus
from app.services.matching_engine import matching_engine
from app.services.websocket_manager import manager
from app.backend.deps import get_current_driver_profile_id, get_current_user_id, require_role
from app.schemas.matching import LocationUpdate, DriverStatusUpdate

class MatchingHttpRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(matching_engine, "/matching")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/driver/register", self.register_driver, methods=["POST"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/feed", self.get_ride_feed, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/notify/{{user_id}}", self.send_notification, methods=["POST"], dependencies=[Depends(require_role('admin'))])
        self.router.add_api_route(f"{self.prefix}/broadcast", self.broadcast_message, methods=["POST"], dependencies=[Depends(require_role('admin'))])
        self.router.add_api_route(f"{self.prefix}/driver/location", self.update_driver_location, methods=["POST"])
        self.router.add_api_route(f"{self.prefix}/driver/status", self.update_driver_status, methods=["POST"])
        self.router.add_api_route(f"{self.prefix}/driver/{{user_id}}/state", self.get_driver_state, methods=["GET"], dependencies=[Depends(require_role(['user', 'driver', 'admin']))])
        self.router.add_api_route(f"{self.prefix}/drivers/stats", self.get_drivers_stats, methods=["GET"], dependencies=[Depends(require_role(['user', 'driver', 'admin']))])

    async def register_driver(self, request: Request, driver_profile_id: int = Depends(get_current_driver_profile_id)) -> Dict[str, Any]:
        profile = await driver_profile_crud.get_by_id(request.state.session, driver_profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Driver profile not found")

        state = driver_tracker.register_driver(
            driver_profile_id=profile.id,
            user_id=profile.user_id,
            classes_allowed=profile.classes_allowed,
            rating=profile.rating_avg,
        )

        return {"status": "registered", "driver_profile_id": state.driver_profile_id, "classes_allowed": list(state.classes_allowed)}

    async def get_ride_feed(self, request: Request, driver_profile_id: int = Depends(get_current_driver_profile_id), limit: int = Query(20, ge=1, le=100)) -> Dict[str, Any]:
        driver = driver_tracker.get_driver(driver_profile_id)
        if not driver:
            return {"driver_profile_id": driver_profile_id, "driver_status": "not_connected", "count": 0, "rides": []}
        
        pending_rides = await ride_crud.get_requested_rides(request.state.session, limit=limit * 2)
        rides_dict = [r.model_dump() for r in pending_rides]
        feed = matching_engine.get_driver_feed(driver_profile_id, rides_dict, limit)
        return {"driver_profile_id": driver_profile_id, "driver_status": driver.status.value, "count": len(feed), "rides": feed}

    async def send_notification(self, user_id: int, message: Dict[str, Any]) -> Dict[str, Any]:
        if not manager.is_connected(user_id):
            raise HTTPException(status_code=404, detail="User not connected")
        await manager.send_personal_message(user_id, {"type": "notification", **message})
        return {"status": "sent", "user_id": user_id}

    async def broadcast_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        await manager.broadcast({"type": "broadcast", **message})
        return {"status": "broadcasted", "recipients": manager.get_connection_count()}

    async def update_driver_location(self, location: LocationUpdate, user_id: int = Depends(get_current_user_id)) -> Dict[str, Any]:
        state = driver_tracker.update_location_by_user_id(user_id=user_id, latitude=location.latitude, longitude=location.longitude)
        if not state:
            raise HTTPException(status_code=404, detail="Driver not registered in tracker")
        return {"status": "updated", "driver_status": state.status.value, "location": {"lat": state.latitude, "lng": state.longitude}}

    async def update_driver_status(self, status_update: DriverStatusUpdate, user_id: int = Depends(get_current_user_id)) -> Dict[str, Any]:
        status = DriverStatus(status_update.status)
        state = driver_tracker.set_status_by_user(user_id, status)
        if not state:
            raise HTTPException(status_code=404, detail="Driver not registered in tracker")
        return {"status": "updated", "driver_status": state.status.value}

    async def get_driver_state(self, user_id: int) -> DriverState:
        state = driver_tracker.get_driver_by_user(user_id)
        if not state:
            raise HTTPException(status_code=404, detail="Driver not found in tracker")

        return state

    async def get_drivers_stats(self) -> Dict[str, Any]:
        return {**driver_tracker.get_stats(), "ws_connections": manager.get_connection_count()}

matching_http_router = MatchingHttpRouter().router
