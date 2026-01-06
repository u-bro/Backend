from typing import Any, Dict
from fastapi import HTTPException, Query, Request, Depends
from app.backend.routers.base import BaseRouter
from app.crud.driver_profile import driver_profile_crud
from app.crud.ride import ride_crud
from app.services.driver_tracker import driver_tracker
from app.services.matching_engine import matching_engine
from app.schemas.matching import DriverRegistration
from app.backend.deps import get_current_driver_profile_id


class MatchingHttpRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(matching_engine, "/matching")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/driver/register", self.register_driver, methods=["POST"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/feed", self.get_ride_feed, methods=["GET"], status_code=200)
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

        return {"status": "registered", "driver_profile_id": state.driver_profile_id, "classes_allowed": list(state.classes_allowed)}

    async def get_ride_feed(self, request: Request, driver_profile_id: int = Depends(get_current_driver_profile_id), limit: int = Query(20, ge=1, le=100)) -> Dict[str, Any]:
        driver = driver_tracker.get_driver(driver_profile_id)
        if not driver:
            return {"driver_profile_id": driver_profile_id, "driver_status": "offline", "count": 0, "rides": []}
        
        pending_rides = await ride_crud.get_requested_rides(request.state.session, limit=limit * 2)
        rides_dict = [r.model_dump() for r in pending_rides]
        feed = matching_engine.get_driver_feed(driver_profile_id, rides_dict, limit)
        return {"driver_profile_id": driver_profile_id, "driver_status": driver.status.value, "count": len(feed), "rides": feed}

    async def get_matching_stats(self) -> Dict[str, Any]:
        return matching_engine.get_stats()


matching_http_router = MatchingHttpRouter().router
