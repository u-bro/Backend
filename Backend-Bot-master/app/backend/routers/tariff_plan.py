from fastapi import Request, Depends

from app.crud.tariff_plan import tariff_plan_crud
from app.schemas.tariff_plan import TariffPlanCreate, TariffPlanSchema, TariffPlanUpdate
from app.backend.routers.base import BaseRouter
from app.backend.deps import require_role


class TariffPlanRouter(BaseRouter):
    def __init__(self, model_crud, prefix) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver","admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role(["admin"]))])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[TariffPlanSchema]:
        return await super().get_paginated(request, page, page_size)

    async def get_by_id(self, request: Request, id: int) -> TariffPlanSchema:
        return await super().get_by_id(request, id)

    async def create(self, request: Request, create_obj: TariffPlanCreate) -> TariffPlanSchema:
        return await super().create(request, create_obj)

    async def update(self, request: Request, id: int, update_obj: TariffPlanUpdate) -> TariffPlanSchema:
        return await super().update(request, id, update_obj)

    async def delete(self, request: Request, id: int) -> TariffPlanSchema:
        return await super().delete(request, id)


tariff_plan_router = TariffPlanRouter(tariff_plan_crud, "/tariff-plans").router
