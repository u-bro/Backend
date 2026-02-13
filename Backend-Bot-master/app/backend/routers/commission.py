from fastapi import Request, Depends
from app.backend.routers.base import BaseRouter
from app.crud.commission import commission_crud
from app.schemas.commission import CommissionSchema, CommissionCreate, CommissionUpdate
from app.backend.deps import require_role
from app.enum import RoleCode


class CommissionRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(commission_crud, "/commissions")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/count", self.get_count, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role([RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role([RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role([RoleCode.ADMIN]))])


    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[CommissionSchema]:
        return await self.model_crud.get_paginated(request.state.session, page, page_size)

    async def get_by_id(self, request: Request, id: int) -> CommissionSchema:
        return await super().get_by_id(request, id)

    async def create(self, request: Request, body: CommissionCreate) -> CommissionSchema:
        return await self.model_crud.create(request.state.session, body)

    async def update(self, request: Request, id: int, body: CommissionUpdate) -> CommissionSchema:
        return await self.model_crud.update(request.state.session, id, body)

    async def delete(self, request: Request, id: int):
        return await self.model_crud.delete(request.state.session, id)


commission_router = CommissionRouter().router
