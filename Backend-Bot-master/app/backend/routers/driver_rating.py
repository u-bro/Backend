from typing import List
from fastapi import Request, Depends
from pydantic import TypeAdapter
from app.backend.routers.base import BaseRouter
from app.crud.driver_rating import driver_rating_crud
from app.schemas.driver_rating import DriverRatingSchema, DriverRatingCreate, DriverRatingUpdate, DriverRatingCreateIn, DriverRatingAvgOut
from app.backend.deps import require_role, require_owner, get_current_user_id
from app.models import DriverRating


class DriverRatingRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(driver_rating_crud, "/driver-ratings")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"])), Depends(require_owner(DriverRating, 'client_id'))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role(["user", "driver", "admin"])), Depends(require_owner(DriverRating, 'client_id'))])
        self.router.add_api_route(f"{self.prefix}/{{driver_id}}/avg", self.get_avg_rating, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[DriverRatingSchema]:
        items = await super().get_paginated(request, page, page_size)
        return TypeAdapter(List[DriverRatingSchema]).validate_python(items)

    async def get_by_id(self, request: Request, item_id: int) -> DriverRatingSchema:
        return await super().get_by_id(request, item_id)

    async def create(self, request: Request, body: DriverRatingCreateIn, user_id: int = Depends(get_current_user_id)) -> DriverRatingSchema:
        body = DriverRatingCreate(client_id=user_id, **body.model_dump())
        return await self.model_crud.create(request.state.session, body)

    async def update(self, request: Request, item_id: int, body: DriverRatingUpdate) -> DriverRatingSchema:
        return await self.model_crud.update(request.state.session, item_id, body)

    async def delete(self, request: Request, item_id: int):
        return await self.model_crud.delete(request.state.session, item_id)

    async def get_avg_rating(self, request: Request, driver_id: int, count: int | None = None) -> DriverRatingAvgOut:
        return await self.model_crud.avg_rating(request.state.session, driver_id, count)

driver_rating_router = DriverRatingRouter().router
