from typing import Any, Dict, List
from fastapi import HTTPException, Query, Request, Depends
from app.backend.routers.base import BaseRouter
from app.crud import driver_profile_crud, driver_location_crud, driver_feed, driver_tracker
from app.services import manager_driver_feed
from app.services.driver_state_storage import driver_state_storage
from app.backend.deps import get_current_driver_profile_id, require_role
from app.schemas.driver_location import DriverLocationSchema, DriverLocationCreate, DriverLocationUpdate, DriverLocationUpdateMe
from app.enum import RoleCode


class MatchingHttpRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(driver_location_crud, "/matching")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/driver/register", self.register_driver, methods=["POST"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/feed", self.get_ride_feed, methods=["GET"], status_code=200)

        self.router.add_api_route(f"{self.prefix}/notify/{{user_id}}", self.send_notification, methods=["POST"], dependencies=[Depends(require_role(RoleCode.ADMIN))])
        self.router.add_api_route(f"{self.prefix}/broadcast", self.broadcast_message, methods=["POST"], dependencies=[Depends(require_role(RoleCode.ADMIN))])

        self.router.add_api_route(f"{self.prefix}/driver-location", self.create, methods=["POST"], dependencies=[Depends(require_role(RoleCode.ADMIN))])
        self.router.add_api_route(f"{self.prefix}/driver-location/{{id}}", self.update, methods=["PUT"], dependencies=[Depends(require_role(RoleCode.ADMIN))])
        self.router.add_api_route(f"{self.prefix}/driver-location", self.update_me, methods=["PUT"])
        self.router.add_api_route(f"{self.prefix}/driver-location", self.get_paginated, methods=["GET"], dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/driver-location/{{id}}", self.get_by_id, methods=["GET"], dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/drivers/stats", self.get_drivers_stats, methods=["GET"], dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])

    async def register_driver(self, request: Request, driver_profile_id: int = Depends(get_current_driver_profile_id)) -> Dict[str, Any]:
        profile = await driver_profile_crud.get_by_id(request.state.session, driver_profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Driver profile not found")

        state = await driver_state_storage.register_driver(request.state.session, profile)

        return {"status": "registered", "driver_profile_id": state.driver_profile_id, "classes_allowed": list(state.classes_allowed)}

    async def get_ride_feed(self, request: Request, driver_profile_id: int = Depends(get_current_driver_profile_id), limit: int = Query(20, ge=1, le=100)) -> Dict[str, Any]:
        driver = driver_state_storage.get_driver(driver_profile_id)
        if not driver:
            return {"driver_profile_id": driver_profile_id, "driver_status": "not_connected", "count": 0, "rides": []}
        
        feed = await driver_feed.get_driver_feed(request.state.session, driver_profile_id, limit)
        return {"driver_profile_id": driver_profile_id, "driver_status": driver.status.value, "count": len(feed), "rides": feed}

    async def send_notification(self, user_id: int, message: Dict[str, Any]) -> Dict[str, Any]:
        if not manager_driver_feed.is_connected(user_id):
            raise HTTPException(status_code=404, detail="User not connected")
        await manager_driver_feed.send_personal_message(user_id, {"type": "notification", **message})
        return {"status": "sent", "user_id": user_id}

    async def broadcast_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        await manager_driver_feed.broadcast({"type": "broadcast", **message})
        return {"status": "broadcasted", "recipients": manager_driver_feed.get_connection_count()}

    async def create(self, request: Request, create_obj: DriverLocationCreate) -> DriverLocationSchema:
        return await self.model_crud.create(request.state.session, create_obj)

    async def update(self, request: Request, update_obj: DriverLocationUpdate, id: int) -> DriverLocationSchema:
        session = request.state.session
        if update_obj.status:
            driver_location = await self.model_crud.get_by_id(session, id)
            await driver_tracker.set_status_by_driver(session, driver_location.driver_profile_id, update_obj.status)
        return await self.model_crud.update(session, id, update_obj)

    async def update_me(self, request: Request, update_obj: DriverLocationUpdateMe, driver_profile_id: int = Depends(get_current_driver_profile_id)) -> DriverLocationSchema:
        session = request.state.session
        if update_obj.status:
            await driver_tracker.set_status_by_driver(session, driver_profile_id, update_obj.status)
        return await self.model_crud.update_me(session, driver_profile_id, update_obj)

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> List[DriverLocationSchema]:
        return await self.model_crud.get_paginated(request.state.session, page, page_size)

    async def get_by_id(self, request: Request, id: int) -> DriverLocationSchema:
        driver_location = await self.model_crud.get_by_id(request.state.session, id)
        if not driver_location:
            raise HTTPException(status_code=404, detail="Driver location not found")
        return driver_location

    async def get_drivers_stats(self) -> Dict[str, Any]:
        return {**driver_state_storage.get_stats(), "ws_connections": manager_driver_feed.get_connection_count()}

matching_http_router = MatchingHttpRouter().router
