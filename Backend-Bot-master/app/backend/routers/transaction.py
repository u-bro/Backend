from typing import List
from fastapi import Request, Depends
from pydantic import TypeAdapter
from app.backend.routers.base import BaseRouter
from app.crud.transaction import transaction_crud
from app.schemas.transaction import TransactionSchema, TransactionCreate, TransactionUpdate
from app.backend.deps import require_role


class TransactionRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(transaction_crud, "/transactions")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role("admin"))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role("admin"))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role("admin"))])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[TransactionSchema]:
        items = await super().get_paginated(request, page, page_size)
        return TypeAdapter(List[TransactionSchema]).validate_python(items)

    async def get_by_id(self, request: Request, id: int) -> TransactionSchema:
        return await super().get_by_id(request, id)

    async def create(self, request: Request, body: TransactionCreate) -> TransactionSchema:
        return await self.model_crud.create(request.state.session, body)

    async def update(self, request: Request, id: int, body: TransactionUpdate) -> TransactionSchema:
        return await self.model_crud.update(request.state.session, id, body)

    async def delete(self, request: Request, id: int):
        return await self.model_crud.delete(request.state.session, id)


transaction_router = TransactionRouter().router
