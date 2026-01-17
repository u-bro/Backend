from typing import List
from fastapi import Request, Depends, HTTPException
from pydantic import TypeAdapter
from app.backend.routers.base import BaseRouter
from app.crud.ride_drivers_request import ride_drivers_request_crud
from app.crud.ride import ride_crud
from app.schemas.ride_drivers_request import RideDriversRequestSchema,RideDriversRequestSchemaWithDriverProfile, RideDriversRequestUpdate
from app.backend.deps import require_role, require_owner
from app.models import Ride, User


class RideDriversRequestRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(ride_drivers_request_crud, "/ride-requests")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/ride/{{id}}", self.get_by_ride_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver","admin"])), Depends(require_owner(Ride, 'client_id'))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200)

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[RideDriversRequestSchema]:
        items = await super().get_paginated(request, page, page_size)
        return TypeAdapter(List[RideDriversRequestSchema]).validate_python(items)

    async def get_by_ride_id(self, request: Request, id: int) -> list[RideDriversRequestSchemaWithDriverProfile]:
        return await self.model_crud.get_by_ride_id_with_driver_profiles(request.state.session, id)

    async def update(self, request: Request, id: int, body: RideDriversRequestUpdate, user: User = Depends(require_role(["user", "driver","admin"]))) -> RideDriversRequestSchema:
        session = request.state.session
        existing = await self.model_crud.get_by_id(session, id)
        if not existing:
            raise HTTPException(status_code=404, detail="Ride request not found")
        ride = await ride_crud.get_by_id(session, existing.ride_id)
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        if user.id != ride.client_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        return await self.model_crud.update(session, id, body)


ride_drivers_request_router = RideDriversRequestRouter().router
