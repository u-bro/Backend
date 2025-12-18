from typing import List
from fastapi import Request, Depends
from pydantic import TypeAdapter
from app.backend.routers.base import BaseRouter
from app.crud.ride import ride_crud
from app.schemas.ride import RideSchema, RideSchemaIn, RideSchemaCreate
from app.backend.deps import require_role, require_ride_client, require_ride_driver, get_current_user_id


class RideRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(ride_crud, "/rides")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role(["user", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role(["admin"]))])
        
        self.router.add_api_route(f"{self.prefix}/{{id}}/client", self.update_by_client, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["user", "admin"])), Depends(require_ride_client)])
        self.router.add_api_route(f"{self.prefix}/{{id}}/driver", self.update_by_driver, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["driver", "admin"])), Depends(require_ride_driver)])
        self.router.add_api_route(f"{self.prefix}/{{id}}/finish", self.finish_ride_by_driver, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["driver", "admin"])), Depends(require_ride_driver)])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[RideSchema]:
        items = await super().get_paginated(request, page, page_size)
        return TypeAdapter(List[RideSchema]).validate_python(items)

    async def get_by_id(self, request: Request, id: int) -> RideSchema:
        return await super().get_by_id(request, id)

    async def create(self, request: Request, create_obj: RideSchemaIn, user_id: int = Depends(get_current_user_id)) -> RideSchema:
        create_obj = RideSchemaCreate(client_id=user_id, **create_obj.model_dump())
        return await super().create(request, create_obj)

    async def update(self, request: Request, id: int, update_obj: RideSchema) -> RideSchema:
        return await super().update(request, id, update_obj)

    async def delete(self, request: Request, id: int) -> RideSchema:
        return await super().delete(request, id)

    async def update(self, request: Request, id: int, update_obj: RideSchema) -> RideSchema:
        return await super().update(request, id, update_obj)

    async def update_by_client(self, request: Request, id: int, update_obj: RideSchema) -> RideSchema:
        return await super().update(request, id, update_obj)

    async def update_by_driver(self, request: Request, id: int, update_obj: RideSchema) -> RideSchema:
        return await super().update(request, id, update_obj)

    async def finish_ride_by_driver(self, request: Request, id: int, update_obj: RideSchema) -> RideSchema:
        return await super().update(request, id, update_obj)

ride_router = RideRouter().router
