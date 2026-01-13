from fastapi import Depends, HTTPException, Request

from app.backend.deps import require_role
from app.backend.routers.base import BaseRouter
from app.crud.device_token import device_token_crud
from app.schemas.push import PushSendToTokenRequest, PushSendToTopicRequest, PushSendToUserRequest
from app.services.fcm_service import fcm_service


class PushAdminRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(device_token_crud, "/push")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/send/token", self.send_to_token, methods=["POST"], status_code=200, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/send/topic", self.send_to_topic, methods=["POST"], status_code=200, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/send/user", self.send_to_user, methods=["POST"], status_code=200, dependencies=[Depends(require_role(["admin"]))])

    async def send_to_token(self, request: Request, body: PushSendToTokenRequest) -> dict:
        message_id = await fcm_service.send_to_token(body)
        return {"message_id": message_id}

    async def send_to_topic(self, request: Request, body: PushSendToTopicRequest) -> dict:
        message_id = await fcm_service.send_to_topic(body)
        return {"message_id": message_id}

    async def send_to_user(self, request: Request, body: PushSendToUserRequest) -> dict:
        tokens = await self.model_crud.get_by_user_id(request.state.session, body.user_id)
        token_values = [t.token for t in tokens]
        if not token_values:
            raise HTTPException(status_code=404, detail="User has no device tokens")

        resp = await fcm_service.send_to_tokens(token_values, body)
        return {"success_count": resp.success_count, "failure_count": resp.failure_count}


push_notification_router = PushAdminRouter().router
