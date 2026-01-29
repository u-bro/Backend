from fastapi import Request, Depends
from app.backend.routers.base import BaseRouter
from app.crud.driver_profile import driver_profile_crud
from app.schemas.driver_profile import DriverProfileSchema, DriverProfileCreate, DriverProfileUpdate, DriverProfileApprove, DriverProfileApproveIn, DriverProfileUpdateMe, DriverProfileWithCars
from app.backend.deps import require_role, get_current_user_id, get_current_driver_profile_id


class DriverProfileRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(driver_profile_crud, "/driver-profiles")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/me", self.get_me, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/me", self.update_me, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}/approve", self.approve_profile, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["admin"]))])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[DriverProfileWithCars]:
        return await self.model_crud.get_paginated_with_cars(request.state.session, page, page_size)

    async def get_by_id(self, request: Request, id: int) -> DriverProfileWithCars:
        return await self.model_crud.get_by_id_with_cars(request.state.session, id)

    async def create(self, request: Request, body: DriverProfileCreate) -> DriverProfileSchema:
        return await self.model_crud.create(request.state.session, body)

    async def update(self, request: Request, id: int, body: DriverProfileUpdate) -> DriverProfileSchema:
        return await self.model_crud.update(request.state.session, id, body)

    async def delete(self, request: Request, id: int):
        return await self.model_crud.delete(request.state.session, id)

    async def approve_profile(self, request: Request, id: int, body: DriverProfileApproveIn, user_id: int = Depends(get_current_user_id)) -> DriverProfileSchema:
        return await self.model_crud.approve(request.state.session, id, DriverProfileApprove(approved_by=user_id, **body.model_dump()))

    async def update_me(self, request: Request, body: DriverProfileUpdateMe, id = Depends(get_current_driver_profile_id)) -> DriverProfileSchema:
        return await self.model_crud.update(request.state.session, id, body)

    async def get_me(self, request: Request, id: int = Depends(get_current_driver_profile_id)) -> DriverProfileSchema:
        return await self.model_crud.get_by_id_with_cars(request.state.session, id)

driver_profile_router = DriverProfileRouter().router
