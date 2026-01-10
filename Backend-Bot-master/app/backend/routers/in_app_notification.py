from typing import List
from fastapi import Request, Depends
from pydantic import TypeAdapter
from app.backend.routers.base import BaseRouter
from app.crud.in_app_notification import in_app_notification_crud
from app.services.websocket_manager import manager
from app.schemas.in_app_notification import InAppNotificationSchema, InAppNotificationCreate, InAppNotificationUpdate
from app.backend.deps import require_role, get_current_user_id


class InAppNotificationRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(in_app_notification_crud, "/notifications/in-app")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/me", self.get_my_notifications, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/me/unread", self.get_my_unread_notifications, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/me/read-all", self.mark_all_as_read, methods=["PUT"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/me/read/{{id}}", self.mark_one_as_read, methods=["PUT"], status_code=200)
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role(["admin"]))])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> List[InAppNotificationSchema]:
        items = await super().get_paginated(request, page, page_size)
        return TypeAdapter(List[InAppNotificationSchema]).validate_python(items)

    async def get_by_id(self, request: Request, id: int) -> InAppNotificationSchema:
        return await super().get_by_id(request, id)

    async def create(self, request: Request, body: InAppNotificationCreate) -> InAppNotificationSchema:
        return await self.model_crud.create(request.state.session, body)

    async def update(self, request: Request, id: int, body: InAppNotificationUpdate) -> InAppNotificationSchema:
        return await self.model_crud.update(request.state.session, id, body)

    async def delete(self, request: Request, id: int):
        return await self.model_crud.delete(request.state.session, id)

    async def get_my_notifications(self, request: Request, page: int = 1, page_size: int = 10, user_id = Depends(get_current_user_id)) -> List[InAppNotificationSchema]:
        return await self.model_crud.get_by_user_id(request.state.session, user_id, page, page_size)

    async def get_my_unread_notifications(self, request: Request, page: int = 1, page_size: int = 10, user_id = Depends(get_current_user_id)) -> List[InAppNotificationSchema]:
        return await self.model_crud.get_unread_by_user_id(request.state.session, user_id, page, page_size)

    async def mark_all_as_read(self, request: Request, user_id = Depends(get_current_user_id)) -> List[InAppNotificationSchema]:
        return await self.model_crud.mark_all_as_read(request.state.session, user_id)

    async def mark_one_as_read(self, request: Request, id: int, user_id = Depends(get_current_user_id)) -> InAppNotificationSchema:
        return await self.model_crud.mark_one_as_read(request.state.session, id, user_id)

in_app_notification_router = InAppNotificationRouter().router
