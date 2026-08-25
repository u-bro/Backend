from fastapi import Request, Depends, HTTPException
from app.backend.routers.base import BaseRouter
from app.crud.ride_drivers_request import ride_drivers_request_crud, RideDriversRequestCrud
from app.crud.ride import ride_crud
from app.schemas.ride_drivers_request import RideDriversRequestSchema, RideDriversRequestSchemaDetailed, RideDriversRequestSchemaWithRide, RideDriversRequestUpdate
from app.schemas.ride import RideExpectedFareUpdate
from app.backend.deps import get_current_driver_profile_id, require_role, require_owner
from app.models import Ride, User
from app.enum import RoleCode


class RideDriversRequestRouter(BaseRouter[RideDriversRequestCrud]):
    def __init__(self, model_crud: RideDriversRequestCrud, prefix: str) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/ride/{{id}}", self.get_by_ride_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN])), Depends(require_owner(Ride, 'client_id'))])
        self.router.add_api_route(f"{self.prefix}/me", self.get_my_requests, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.DRIVER]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200)

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[RideDriversRequestSchema]:
        return await self.model_crud.get_paginated(request.state.session, page, page_size)

    async def get_by_ride_id(self, request: Request, id: int) -> list[RideDriversRequestSchemaDetailed]:
        return await self.model_crud.get_by_ride_id_detailed(request.state.session, id)

    async def get_my_requests(self, request: Request, status: str = "requested", driver_profile_id: int = Depends(get_current_driver_profile_id)) -> list[RideDriversRequestSchemaWithRide]:
        if status != "requested":
            raise HTTPException(status_code=400, detail="VALIDATION_ERROR")
        return await self.model_crud.get_requested_with_ride_by_driver_profile_id(request.state.session, driver_profile_id)

    async def update(self, request: Request, id: int, body: RideDriversRequestUpdate, user: User = Depends(require_role([RoleCode.USER]))) -> RideDriversRequestSchema:
        session = request.state.session
        existing = await self.model_crud.get_by_id(session, id)
        if not existing:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        ride = await ride_crud.get_by_id(session, existing.ride_id)
        if not ride:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        if user.id != ride.client_id:
            raise HTTPException(status_code=403, detail="FORBIDDEN")

        return await self.model_crud.update(session, id, body)


ride_drivers_request_router = RideDriversRequestRouter(ride_drivers_request_crud, "/ride-requests").router
