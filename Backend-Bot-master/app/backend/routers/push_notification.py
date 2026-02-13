from fastapi import Depends, Request
from app.backend.deps import require_role
from app.backend.routers.base import BaseRouter
from app.schemas.push import PushSendToTokenRequest, PushSendToTopicRequest, PushSendToUserRequest
from app.services.fcm_service import fcm_service
from app.enum import RoleCode


class PushAdminRouter(BaseRouter[None]):
    def __init__(self, model_crud: None, prefix: str) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/send/token", self.send_to_token, methods=["POST"], status_code=200, dependencies=[Depends(require_role([RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/send/topic", self.send_to_topic, methods=["POST"], status_code=200, dependencies=[Depends(require_role([RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/send/user", self.send_to_user, methods=["POST"], status_code=200, dependencies=[Depends(require_role([RoleCode.ADMIN]))])

    async def send_to_token(self, request: Request, body: PushSendToTokenRequest) -> dict:
        message_id = await fcm_service.send_to_token(body)
        return {"message_id": message_id}

    async def send_to_topic(self, request: Request, body: PushSendToTopicRequest) -> dict:
        message_id = await fcm_service.send_to_topic(body)
        return {"message_id": message_id}

    async def send_to_user(self, request: Request, body: PushSendToUserRequest) -> dict:
        resp = await fcm_service.send_to_user(request.state.session, body.user_id, body)
        return {"success_count": resp.success_count, "failure_count": resp.failure_count}


push_notification_router = PushAdminRouter(None, "/push").router
