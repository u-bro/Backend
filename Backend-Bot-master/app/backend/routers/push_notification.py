import hmac
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select

from app.backend.deps import require_role
from app.backend.routers.base import BaseRouter
from app.config import PUSH_INTERNAL_TOKEN
from app.crud.device_token import device_token_crud
from app.models import AdminPushNotification, User
from app.schemas.push import AdminPushSendRequest, AdminPushSendResponse, PushNotificationData, PushSendToTokenRequest, PushSendToTopicRequest, PushSendToUserRequest
from app.services.fcm_service import fcm_service
from app.enum import RoleCode


class PushAdminRouter(BaseRouter[None]):
    def __init__(self, model_crud: None, prefix: str) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/send/token", self.send_to_token, methods=["POST"], status_code=200, dependencies=[Depends(require_role([RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/send/topic", self.send_to_topic, methods=["POST"], status_code=200, dependencies=[Depends(require_role([RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/send/user", self.send_to_user, methods=["POST"], status_code=200, dependencies=[Depends(require_role([RoleCode.ADMIN]))])
        self.router.add_api_route(f"/internal{self.prefix}/send", self.send_from_admin, methods=["POST"], status_code=200, response_model=AdminPushSendResponse)

    async def send_to_token(self, request: Request, body: PushSendToTokenRequest) -> dict:
        message_id = await fcm_service.send_to_token(body)
        return {"message_id": message_id}

    async def send_to_topic(self, request: Request, body: PushSendToTopicRequest) -> dict:
        message_id = await fcm_service.send_to_topic(body)
        return {"message_id": message_id}

    async def send_to_user(self, request: Request, body: PushSendToUserRequest) -> dict:
        resp = await fcm_service.send_to_user(request.state.session, body.user_id, body)
        return {"success_count": resp.success_count if resp else 0, "failure_count": resp.failure_count if resp else 0}

    async def send_from_admin(
        self,
        request: Request,
        body: AdminPushSendRequest,
        x_push_internal_token: str | None = Header(None, alias="X-Push-Internal-Token"),
    ) -> AdminPushSendResponse:
        if not PUSH_INTERNAL_TOKEN or not x_push_internal_token or not hmac.compare_digest(PUSH_INTERNAL_TOKEN, x_push_internal_token):
            raise HTTPException(status_code=403, detail="Invalid push internal token")

        session = request.state.session
        if body.user_id is not None:
            user_exists = await session.scalar(select(User.id).where(User.id == body.user_id))
            if user_exists is None:
                raise HTTPException(status_code=404, detail="User not found")

        history = AdminPushNotification(
            audience=body.audience,
            target_user_id=body.user_id,
            title=body.title,
            body=body.body,
            operator_id=body.operator_id,
            operator_name=body.operator_name,
            status="processing",
            recipient_user_count=0,
            attempted_token_count=0,
            success_count=0,
            failure_count=0,
        )
        session.add(history)
        await session.flush()
        await session.commit()
        history_id = history.id

        try:
            tokens, recipient_user_count = await device_token_crud.get_recipients(session, body.user_id)
            result = await fcm_service.send_to_tokens_batched(
                tokens,
                PushNotificationData(title=body.title, body=body.body),
            )
            if result.attempted_count == 0:
                status = "failed"
            elif result.failure_count == 0:
                status = "sent"
            elif result.success_count:
                status = "partial"
            else:
                status = "failed"
            history.status = status
            history.recipient_user_count = recipient_user_count
            history.attempted_token_count = result.attempted_count
            history.success_count = result.success_count
            history.failure_count = result.failure_count
            history.error_message = (
                "; ".join(result.errors)[:2000]
                or ("No device tokens" if result.attempted_count == 0 else None)
            )
            history.completed_at = datetime.now(timezone.utc)
            await session.flush()
        except Exception as exc:
            await session.rollback()
            history = await session.get(AdminPushNotification, history_id)
            history.status = "failed"
            history.error_message = f"Push result unknown: {type(exc).__name__}"
            history.completed_at = datetime.now(timezone.utc)
            await session.commit()

        return AdminPushSendResponse(
            history_id=history.id,
            status=history.status,
            recipient_user_count=history.recipient_user_count,
            attempted_token_count=history.attempted_token_count,
            success_count=history.success_count,
            failure_count=history.failure_count,
        )


push_notification_router = PushAdminRouter(None, "/push").router
