from typing import List
from fastapi import Request, HTTPException, Depends
from pydantic import TypeAdapter
from app.backend.routers.base import BaseRouter
from app.crud.role import role_crud
from app.schemas.role import RoleSchema, RoleCreate, RoleUpdate
from app.backend.deps import require_role


class RoleRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(role_crud, "/roles")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver","admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role(["admin"]))])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[RoleSchema]:
        items = await super().get_paginated(request, page, page_size)
        return TypeAdapter(List[RoleSchema]).validate_python(items)

    async def get_by_id(self, request: Request, item_id: int) -> RoleSchema:
        return await super().get_by_id(request, item_id)

    async def create_role(self, request: Request, body: RoleCreate) -> RoleSchema:
        return await self.model_crud.create(request.state.session, body)

    async def update_role(self, request: Request, item_id: int, body: RoleUpdate) -> RoleSchema:
        return await self.model_crud.update(request.state.session, item_id, body)

    async def delete_role(self, request: Request, item_id: int):
        result = await self.model_crud.delete(request.state.session, item_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Role not found")
        return result


role_router = RoleRouter().router
