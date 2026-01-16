from typing import List
from fastapi import Request, Depends
from pydantic import TypeAdapter
from app.backend.routers.base import BaseRouter
from app.crud.ride_drivers_request import ride_drivers_request_crud
from app.schemas.ride_drivers_request import RideDriversRequestSchema, RideDriversRequestUpdate
from app.backend.deps import require_role, require_owner
from app.models import Ride


class RideDriversRequestRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(ride_drivers_request_crud, "/ride-requests")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/ride/{{id}}", self.get_by_ride_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver","admin"])), Depends(require_owner(Ride, 'client_id'))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["admin"]))])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[RideDriversRequestSchema]:
        items = await super().get_paginated(request, page, page_size)
        return TypeAdapter(List[RideDriversRequestSchema]).validate_python(items)

    async def get_by_ride_id(self, request: Request, id: int) -> list[RideDriversRequestSchema]:
        return await self.model_crud.get_by_ride_id(request.state.session, id)

    async def update(self, request: Request, id: int, body: RideDriversRequestUpdate) -> RideDriversRequestSchema:
        return await self.model_crud.update(request.state.session, id, body)


ride_drivers_request_router = RideDriversRequestRouter().router
