from typing import List
from fastapi import Request, Depends
from pydantic import TypeAdapter
from app.backend.routers.base import BaseRouter
from app.crud.driver_location import driver_location_crud
from app.schemas.driver_location import DriverLocationSchema, DriverLocationCreate, DriverLocationUpdate
from app.backend.deps import require_role, require_driver_profile, require_driver_verification
from app.models import DriverLocation


class DriverLocationRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(driver_location_crud, "/driver-locations")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role(["driver", "admin"])), Depends(require_driver_verification)])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["driver", "admin"])), Depends(require_driver_verification), Depends(require_driver_profile(DriverLocation))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role(["driver", "admin"])), Depends(require_driver_verification), Depends(require_driver_profile(DriverLocation))])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[DriverLocationSchema]:
        items = await super().get_paginated(request, page, page_size)
        return TypeAdapter(List[DriverLocationSchema]).validate_python(items)

    async def get_by_id(self, request: Request, id: int) -> DriverLocationSchema:
        return await super().get_by_id(request, id)

    async def create(self, request: Request, body: DriverLocationCreate) -> DriverLocationSchema:
        return await self.model_crud.create(request.state.session, body)

    async def update(self, request: Request, id: int, body: DriverLocationUpdate) -> DriverLocationSchema:
        return await self.model_crud.update(request.state.session, id, body)

    async def delete(self, request: Request, id: int):
        return await self.model_crud.delete(request.state.session, id)


driver_location_router = DriverLocationRouter().router
