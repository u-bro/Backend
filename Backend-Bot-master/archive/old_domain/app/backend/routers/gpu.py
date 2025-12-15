from typing import List, Optional
from fastapi import Query, Request
from pydantic import TypeAdapter

from app.crud import gpu_crud
from app.schemas import GpuSchema, GpuSchemaCreate
from app.backend.routers.base import BaseRouter
from app.schemas.gpu import GpuGetPaginatedWithFiltersRequest 


class GpuRouter(BaseRouter):
    def __init__(self, model_crud, prefix) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated_with_filters, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/count", self.get_count, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200)

    async def get_count(self, request: Request) -> int:
        return await super().get_count(request)

    async def get_by_id(self, request: Request, id: int) -> GpuSchema:
        return await super().get_by_id(request, id)

    async def update(self, request: Request, id: int, update_obj: GpuSchema) -> GpuSchema:
        return await super().update(request, id, update_obj)

    async def get_paginated_with_filters(
        self,
        request: Request,
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1),
        sort_by: Optional[str] = Query(None),
        sort_desc: bool = Query(False),
        price_from: Optional[int] = Query(None),
        price_to: Optional[int] = Query(None),
        income_from: Optional[int] = Query(None),
        income_to: Optional[int] = Query(None),
        show_crafted: Optional[bool] = Query(None),
        rarity: Optional[List[int]] = Query(None)
    ):
        filters = {
            "price": {"from": price_from, "to": price_to},
            "income": {"from": income_from, "to": income_to},
            "is_crafted": show_crafted,
            "rarity": rarity or []
        }
        filters = {k: v for k, v in filters.items() if v is not None}
    
        result = await self.model_crud.get_paginated_with_filters(
            session=request.state.session,
            page=page,
            page_size=page_size,
            filters=filters,
            sort_by=sort_by,
            sort_desc=sort_desc
        )

        return TypeAdapter(List[GpuSchema]).validate_python(result)

gpu_router = GpuRouter(gpu_crud, "/gpus").router
