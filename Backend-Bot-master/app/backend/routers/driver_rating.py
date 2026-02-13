import app.config
from fastapi import Request, Depends
from app.backend.routers.base import BaseRouter
from app.crud.driver_rating import driver_rating_crud, DriverRatingCrud
from app.schemas.driver_rating import DriverRatingSchema, DriverRatingCreate, DriverRatingUpdate, DriverRatingCreateIn, DriverRatingAvgOut, DriverRatingConfig
from app.backend.deps import require_role, require_owner, get_current_user_id
from app.models import DriverRating
from app.enum import RoleCode


class DriverRatingRouter(BaseRouter[DriverRatingCrud]):
    def __init__(self, model_crud: DriverRatingCrud, prefix: str) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/config", self.configure_rating_consts, methods=["PUT"], status_code=200, dependencies=[Depends(require_role([RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN])), Depends(require_owner(DriverRating, 'client_id'))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN])), Depends(require_owner(DriverRating, 'client_id'))])
        self.router.add_api_route(f"{self.prefix}/{{driver_id}}/avg", self.get_avg_rating, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[DriverRatingSchema]:
        return await self.model_crud.get_paginated(request.state.session, page, page_size)

    async def get_by_id(self, request: Request, id: int) -> DriverRatingSchema:
        return await super().get_by_id(request, id)

    async def create(self, request: Request, body: DriverRatingCreateIn, user_id: int = Depends(get_current_user_id)) -> DriverRatingSchema:
        body = DriverRatingCreate(client_id=user_id, **body.model_dump())
        return await self.model_crud.create(request.state.session, body)

    async def update(self, request: Request, id: int, body: DriverRatingUpdate) -> DriverRatingSchema:
        return await self.model_crud.update(request.state.session, id, body)

    async def delete(self, request: Request, id: int):
        return await self.model_crud.delete(request.state.session, id)

    async def get_avg_rating(self, request: Request, driver_id: int, count: int | None = None) -> DriverRatingAvgOut:
        return await self.model_crud.avg_rating(request.state.session, driver_id, count)

    async def configure_rating_consts(self, request: Request, body: DriverRatingConfig):
        app.config.RATING_AVG_COUNT = body.rating_avg_count
        await self.model_crud.recalculate_rating_avg(request.state.session)
        return {"ok": True}

driver_rating_router = DriverRatingRouter(driver_rating_crud, "/driver-ratings").router
