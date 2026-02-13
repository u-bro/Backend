from fastapi import Request, Depends
from app.backend.routers.base import BaseRouter
from app.crud.ride_status_history import ride_status_history_crud
from app.schemas.ride_status_history import RideStatusHistorySchema, RideStatusHistoryCreate
from app.backend.deps import require_role
from app.enum import RoleCode


class RideStatusHistoryRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(ride_status_history_crud, "/ride-status-history")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role([RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role([RoleCode.ADMIN]))])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[RideStatusHistorySchema]:
        return await self.model_crud.get_paginated(request.state.session, page, page_size)

    async def get_by_id(self, request: Request, id: int) -> RideStatusHistorySchema:
        return await super().get_by_id(request, id)

    async def create(self, request: Request, body: RideStatusHistoryCreate) -> RideStatusHistorySchema:
        return await self.model_crud.create(request.state.session, body)

    async def delete(self, request: Request, id: int):
        return await self.model_crud.delete(request.state.session, id)


ride_status_history_router = RideStatusHistoryRouter().router
