from fastapi import Request
from fastapi.responses import JSONResponse

from app.crud import user_gpu_storage_crud
from app.schemas import UserGpuStorageSchema, UserGpuStorageSchemaCreate, UserGpuStorageSchemaUpdate
from app.backend.routers.base import BaseRouter


class UserGpuStorageRouter(BaseRouter):
    def __init__(self, model_crud, prefix) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/{{user_id}}", self.get_paginated_storage, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/purchase", self.purchase_gpu_from_default_shop, methods=["POST"], status_code=201, description='Purchase gpu')
        self.router.add_api_route(f"{self.prefix}/sell", self.sell_gpu_half_price, methods=["DELETE"], status_code=202, description="Sell gpu")
        self.router.add_api_route(f"{self.prefix}/craft", self.craft_gpu, methods=["POST"], status_code=201, description="Craft gpu from 5 or less")
        self.router.add_api_route(f"{self.prefix}/mount/{{user_gpu_schema_id}}", self.mount_gpu, methods=["PATCH"], status_code=200, description="For remove or add is_active status")

    async def get_paginated_storage(self, request: Request, user_id: int, page: int = 1, page_size: int = 2, is_working: bool = None):
        return await user_gpu_storage_crud.get_paginated_storage(request.state.session, user_id, page, page_size, is_working)

    async def sell_gpu_half_price(self, request: Request, user_gpu_storage_id: int) -> bool:
        return await user_gpu_storage_crud.sell_gpu_half_price(request.state.session, user_gpu_storage_id)

    async def mount_gpu(self, request: Request, user_gpu_storage_id: int, user_gpu_storage: UserGpuStorageSchemaUpdate) -> JSONResponse:
        result = await user_gpu_storage_crud.mount_gpu(request.state.session, user_gpu_storage_id, user_gpu_storage)
        if result:
            return result
        return JSONResponse(status_code=400, content={"detail": "This item does not exist or it cannot assign more than 4 gpus"})

    async def purchase_gpu_from_default_shop(self, request: Request, user_id: int, gpu_id: int):
        result = await user_gpu_storage_crud.purchase_gpu(request.state.session, user_id, gpu_id)
        if result:
            return result
        return JSONResponse(status_code=400, content={"detail": "Not enough money or something went wrong"})

    async def craft_gpu(self, request: Request, gpu_ids: list[int], user_id: int):
        gpu_ids = gpu_ids + [None] * (5 - len(gpu_ids)) if 1 <= len(gpu_ids) <= 5 else gpu_ids
        result = await user_gpu_storage_crud.craft_gpu(request.state.session, gpu_ids, user_id)
        if result in ['Craft successful! You received a crafted GPU.', 'Craft failed. You received a fallback GPU.']:
            return result
        return JSONResponse(status_code=400, content={"detail": result})


users_gpus_storage_router = UserGpuStorageRouter(user_gpu_storage_crud, "/gpu-storages").router
