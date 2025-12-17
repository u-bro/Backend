from typing import List
from fastapi import Request, HTTPException, Depends
from pydantic import TypeAdapter
from starlette.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from app.backend.routers.base import BaseRouter
from app.crud.driver_location import driver_location_crud
from app.schemas.driver_location import DriverLocationSchema, DriverLocationCreate, DriverLocationUpdate
from app.backend.deps import require_role, require_driver_location_owner


class DriverLocationRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(driver_location_crud, "/driver-locations")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role(["driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["driver", "admin"])), Depends(require_driver_location_owner)])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role(["driver", "admin"])), Depends(require_driver_location_owner)])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[DriverLocationSchema]:
        items = await super().get_paginated(request, page, page_size)
        return TypeAdapter(List[DriverLocationSchema]).validate_python(items)

    async def get_by_id(self, request: Request, item_id: int) -> DriverLocationSchema:
        return await super().get_by_id(request, item_id)

    async def create_item(self, request: Request, body: DriverLocationCreate) -> DriverLocationSchema:
        try:
            return await self.model_crud.create(request.state.session, body)
        except IntegrityError as e:
            await request.state.session.rollback()
            if "foreign key" in str(e.orig).lower():
                raise HTTPException(status_code=422, detail="Referenced driver profile does not exist")
            raise HTTPException(status_code=422, detail=str(e.orig))

    async def update_item(self, request: Request, item_id: int, body: DriverLocationUpdate) -> DriverLocationSchema:
        return await self.model_crud.update(request.state.session, item_id, body)

    async def delete_item(self, request: Request, item_id: int):
        item = await self.model_crud.delete(request.state.session, item_id)
        if item is None:
            return JSONResponse(status_code=404, content={"detail": "Item not found"})
        return item


driver_location_router = DriverLocationRouter().router
