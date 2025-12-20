from typing import List
from fastapi import Request, Depends
from pydantic import TypeAdapter
from starlette.responses import JSONResponse
from app.backend.routers.base import BaseRouter
from app.crud.chat_message import chat_message_crud
from app.schemas.chat_message import ChatMessageSchema, ChatMessageCreate, ChatMessageUpdate
from app.backend.deps import require_role, require_chat_message_owner


class ChatMessageRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(chat_message_crud, "/chat-messages")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/count", self.get_count, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"])), Depends(require_chat_message_owner)])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role(["user", "driver", "admin"])), Depends(require_chat_message_owner)])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[ChatMessageSchema]:
        items = await super().get_paginated(request, page, page_size)
        return TypeAdapter(List[ChatMessageSchema]).validate_python(items)

    async def get_by_id(self, request: Request, item_id: int) -> ChatMessageSchema:
        return await super().get_by_id(request, item_id)

    async def create_item(self, request: Request, body: ChatMessageCreate) -> ChatMessageSchema:
        return await self.model_crud.create(request.state.session, body)

    async def update_item(self, request: Request, item_id: int, body: ChatMessageUpdate) -> ChatMessageSchema:
        return await self.model_crud.update(request.state.session, item_id, body)

    async def delete_item(self, request: Request, item_id: int):
        user_id = request.query_params.get("user_id")
        msg = await self.model_crud.get_by_id(request.state.session, item_id)
        if msg is None:
            return JSONResponse(status_code=404, content={"detail": "Item not found"})
        if user_id is not None and str(msg.sender_id) != str(user_id):
            return JSONResponse(status_code=403, content={"detail": "Forbidden: not the owner"})
        item = await self.model_crud.delete(request.state.session, item_id)
        return item


chat_message_router = ChatMessageRouter().router
