from fastapi import Request
from fastapi.responses import JSONResponse

from app.crud import order_crud
from app.schemas import OrderSchema, OrderSchemaCreate, OrderSchemaUpdate
from app.backend.routers.base import BaseRouter


class OrderRouter(BaseRouter):
    def __init__(self, model_crud, prefix) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/count", self.get_count, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201)
        self.router.add_api_route(f"{self.prefix}-purchase", self.purchase_gpu_by_order, methods=["POST"], status_code=201)
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202)
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200)
        self.router.add_api_route(f"{self.prefix}-batch", self.batch_delete, methods=["DELETE"], status_code=202)

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 2) -> list[OrderSchema]:
        return await super().get_paginated(request, page, page_size)

    async def get_count(self, request: Request) -> int:
        return await super().get_count(request)

    async def get_by_id(self, request: Request, id: int) -> OrderSchema:
        return await super().get_by_id(request, id)

    async def create(self, request: Request, create_obj: OrderSchemaCreate) -> OrderSchema:
        return await super().create(request, create_obj)

    async def delete(self, request: Request, id: int) -> int:
        return await super().delete(request, id)

    async def update(self, request: Request, id: int, update_obj: OrderSchemaUpdate) -> OrderSchema:
        return await super().update(request, id, update_obj)

    async def batch_delete(self, request: Request, ids: list[int]):
        return await super().batch_delete(request, ids)

    async def purchase_gpu_by_order(self, request: Request, buyer_id: int, order_id: int):
        result = await order_crud.purchase_gpu_by_order(request.state.session, buyer_id, order_id)
        if result:
            return result
        return JSONResponse(status_code=400, content={"detail": "Problem with selling GPU by order"})


order_router = OrderRouter(order_crud, "/orders").router
