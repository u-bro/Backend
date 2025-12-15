from typing import TypeVar

from fastapi import APIRouter, HTTPException, Request
from starlette.responses import JSONResponse

from app.crud import CrudBase


T = TypeVar('T')


class BaseRouter:
    def __init__(self, model_crud: CrudBase, prefix: str) -> None:
        self.router = APIRouter()
        self.model_crud = model_crud
        self.prefix = prefix
        self.setup_routes()

    def setup_routes(self) -> None:
        raise NotImplemented

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 2) -> list[T]:
        return await self.model_crud.get_paginated(request.state.session, page, page_size)

    async def get_count(self, request: Request) -> int:
        return await self.model_crud.get_count(request.state.session)

    async def get_by_id(self, request: Request, id: int) -> T:
        item = await self.model_crud.get_by_id(request.state.session, id)
        if item is None:
            return JSONResponse(status_code=404, content="Item not found")
        return item

    async def create(self, request: Request, create_obj: T) -> T:
        return await self.model_crud.create(request.state.session, create_obj)

    async def delete(self, request: Request, id: int) -> T:
        item = await self.model_crud.delete(request.state.session, id)
        if item is None:
            return JSONResponse(status_code=404, content="Item not found")
        return item

    async def update(self, request: Request, id: int, update_obj: T) -> T:
        item = await self.model_crud.update(request.state.session, id, update_obj)
        if item is None:
            return JSONResponse(status_code=404, content="Item not found")
        return item

    async def batch_create(self, request: Request, create_objs: list[T]) -> list[T]:
        return await self.model_crud.batch_create(request.state.session, create_objs)

    async def batch_delete(self, request: Request, ids: list[int]) -> list[int]:
        return await self.model_crud.batch_delete(request.state.session, ids)
