from typing import Any, Dict, Optional
from fastapi import HTTPException, Query, Request, Depends
from app.backend.routers.base import BaseRouter
from app.schemas.chat_message import ChatHistoryResponse, SendMessageRequest, SendMessageResponse
from app.services.chat_service import chat_service
from app.backend.deps import get_current_user_id
from app.services.websocket_manager import manager


class ChatHttpRouter(BaseRouter):
    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/{{ride_id}}/history", self.get_chat_history, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{ride_id}}/send", self.send_message, methods=["POST"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{ride_id}}/message/{{message_id}}", self.delete_message, methods=["DELETE"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{ride_id}}/message/{{message_id}}", self.edit_message, methods=["PUT"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/stats", self.get_chat_stats, methods=["GET"], status_code=200)

    def __init__(self) -> None:
        super().__init__(chat_service, "/chat")

    async def get_chat_history(self, request: Request, ride_id: int, limit: int = Query(50, ge=1, le=100), before_id: Optional[int] = Query(None, description="message id")) -> ChatHistoryResponse:
        session = request.state.session

        messages = await chat_service.get_chat_history(
            session=session,
            ride_id=ride_id,
            limit=limit + 1,
            before_id=before_id,
        )

        has_more = len(messages) > limit
        if has_more:
            messages = messages[1:]

        return ChatHistoryResponse(
            ride_id=ride_id,
            messages=[
                {
                    "id": m.id,
                    "sender_id": m.sender_id,
                    "text": m.text,
                    "message_type": m.message_type,
                    "is_moderated": m.is_moderated,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "edited_at": m.edited_at.isoformat() if m.edited_at else None,
                    "deleted": m.deleted_at is not None,
                }
                for m in messages
            ],
            count=len(messages),
            has_more=has_more,
        )

    async def send_message(self, request: Request, ride_id: int, body: SendMessageRequest, sender_id: int = Depends(get_current_user_id)) -> SendMessageResponse:
        session = request.state.session
        allowed, error = chat_service.check_rate_limit(sender_id)
        if not allowed:
            raise HTTPException(status_code=429, detail=error)
        moderation = chat_service.moderate_message(body.text)

        if not moderation.passed:
            raise HTTPException(status_code=400, detail=moderation.reason)

        message = await chat_service.save_message(
            session=session,
            ride_id=ride_id,
            sender_id=sender_id,
            text=moderation.filtered,
            message_type=body.message_type,
            attachments=body.attachments,
            is_moderated=True,
        )

        await manager.send_to_ride(ride_id, {"type": "new_message", "message": {"id": message.id, "ride_id": ride_id, "sender_id": sender_id, "text": message.text, "message_type": message.message_type, "created_at": message.created_at.isoformat() if message.created_at else None}})

        return SendMessageResponse(
            id=message.id,
            ride_id=ride_id,
            sender_id=sender_id,
            text=message.text,
            message_type=message.message_type,
            is_moderated=message.is_moderated,
            created_at=message.created_at,
            moderation_note="Censored" if moderation.original != moderation.filtered else None,
        )

    async def delete_message(self, request: Request, ride_id: int, message_id: int, user_id: int = Depends(get_current_user_id)) -> Dict[str, Any]:
        session = request.state.session
        await chat_service.soft_delete_message(session=session, message_id=message_id, user_id=user_id)
        await manager.send_to_ride(ride_id, {"type": "message_deleted", "message_id": message_id, "deleted_by": user_id})
        return {"status": "deleted", "message_id": message_id}

    async def edit_message(self, request: Request, ride_id: int, message_id: int, body: SendMessageRequest, user_id: int = Depends(get_current_user_id)) -> Dict[str, Any]:
        session = request.state.session
        message = await chat_service.edit_message(session=session, message_id=message_id, user_id=user_id, new_text=body.text)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found or you don't have permission")

        await manager.send_to_ride(ride_id, {"type": "message_edited", "message": {"id": message.id, "text": message.text, "edited_at": message.edited_at.isoformat() if message.edited_at else None}})

        return {"status": "edited", "message": {"id": message.id, "text": message.text, "edited_at": message.edited_at}}

    async def get_chat_stats(self) -> Dict[str, Any]:
        return chat_service.get_stats()


chat_http_router = ChatHttpRouter().router
