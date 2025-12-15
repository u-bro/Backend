"""ARCHIVED: original content moved to archive/old_domain/app/backend/routers/gpu.py

This file was archived during cleanup. See archive/old_domain/app/backend/routers/gpu.py for original implementation.
"""

raise ImportError("This module has been archived. See archive/old_domain/app/backend/routers/gpu.py")


class GpuRouter(BaseRouter):
    def __init__(self, model_crud, prefix) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated_with_filters, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/count", self.get_count, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200)
        # self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201)
        # self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202)
        # self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200)
        # self.router.add_api_route(f"{self.prefix}/batch", self.batch_create, methods=["POST"], status_code=201)
        # self.router.add_api_route(f"{self.prefix}/batch", self.batch_delete, methods=["DELETE"], status_code=202)

    # async def get_paginated(self, request: Request, page: int = 1, page_size: int = 2) -> list[GpuSchema]:
    #     return await super().get_paginated(request, page, page_size)

    async def get_count(self, request: Request) -> int:
        return await super().get_count(request)

    async def get_by_id(self, request: Request, id: int) -> GpuSchema:
        return await super().get_by_id(request, id)

    # async def create(self, request: Request, create_obj: GpuSchemaCreate) -> GpuSchema:
    #     return await super().create(request, create_obj)

    # async def delete(self, request: Request, id: int) -> int:
    #     return await super().delete(request, id)

    async def update(self, request: Request, id: int, update_obj: GpuSchema) -> GpuSchema:
        return await super().update(request, id, update_obj)

    # async def batch_create(self, request: Request, create_objs: list[GpuSchemaCreate]) -> list[GpuSchema]:
    #     return await super().batch_create(request, create_objs)
    #
    # async def batch_delete(self, request: Request, ids: list[int]) -> list[int]:
    #     return await super().batch_delete(request, ids)

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
            "rarity": rarity or []  # Если None, подставляем пустой список
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
